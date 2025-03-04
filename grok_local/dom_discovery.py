#!/usr/bin/env python3
# grok_local/dom_discovery.py
import json
import logging
import os
import requests
import subprocess
import time
from bs4 import BeautifulSoup
from grok_local.config import logger, BROWSER_BACKEND
from grok_local.browser_adapter import BrowserAdapter
from grok_local.ai_adapters import get_ai_adapter

def ensure_ollama_running(model):
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json()["models"]]
            if f"{model}:latest" not in models:
                logger.info(f"Pulling model {model}...")
                subprocess.run(["ollama", "pull", model], check=True)
            logger.info("Ollama is running and model is available")
            return True
    except (requests.ConnectionError, subprocess.CalledProcessError):
        logger.info("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"])
        time.sleep(5)
        try:
            logger.info(f"Pulling model {model}...")
            subprocess.run(["ollama", "pull", model], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull model {model}: {str(e)}")
            return False
    return False

def discover_dom(url, output_json, html_dir=None, use_browser=False, force=False, model="deepseek-r1", retries=3):
    elements = []
    html = None
    html_file = os.path.join(html_dir, "saved_resource.html") if html_dir else None

    if html_file and os.path.exists(html_file) and not force:
        logger.info(f"Using existing HTML file: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        if use_browser:
            for attempt in range(retries):
                try:
                    browser = BrowserAdapter(BROWSER_BACKEND)
                    logger.info(f"Attempt {attempt + 1}/{retries}: Loading {url} dynamically with {BROWSER_BACKEND}")
                    browser.goto(url)
                    time.sleep(5)
                    if BROWSER_BACKEND == "PLAYWRIGHT":
                        html = browser.driver.content()
                    elif BROWSER_BACKEND == "SELENIUM":
                        html = browser.driver.page_source
                    else:
                        html = browser.driver.page_source if hasattr(browser.driver, 'page_source') else browser.driver.content()
                    browser.close()
                    break
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == retries - 1:
                        logger.error("All retries failed; falling back to static fetch")
                        html = fetch_static(url)
                        if not html:
                            return
                    else:
                        time.sleep(2)
        else:
            html = fetch_static(url)
            if not html:
                return

        if html and html_file:
            os.makedirs(os.path.dirname(html_file), exist_ok=True)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved HTML to {html_file}")

    if not html:
        logger.error("No HTML content available to process")
        return

    soup = BeautifulSoup(html, 'html.parser')
    logger.info("Parsing HTML with BeautifulSoup")

    for tag in soup.find_all(['input', 'textarea', 'button', 'form', 'div', 'p', 'span']):
        element = {
            "tag": tag.name,
            "text": tag.get_text(strip=True)[:50],
            "attributes": dict(tag.attrs),
            "selector": _generate_selector(tag),
            "candidate_role": _identify_candidate_role(tag)
        }
        if element["text"] or element["attributes"]:
            elements.append(element)

    logger.info(f"Found {len(elements)} elements")

    if not ensure_ollama_running(model):
        logger.error(f"Could not start Ollama with model {model}")
        return

    agent_suggestions = _get_agent_suggestions(url, html, elements, model)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"url": url, "elements": elements, "agent_suggestions": agent_suggestions}, f, indent=2)
    logger.info(f"DOM elements and agent suggestions saved to {output_json}")

def fetch_static(url):
    try:
        logger.info(f"Fetching {url} statically")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Static DOM fetch failed: {str(e)}")
        return None

def _generate_selector(tag):
    if tag.get('id'):
        return f"#{tag['id']}"
    elif tag.get('class'):
        return f"{tag.name}.{'.'.join(tag['class'])}"
    else:
        return tag.name

def _identify_candidate_role(tag):
    text = tag.get_text(strip=True).lower()
    attrs = {k.lower(): v.lower() if isinstance(v, str) else v for k, v in tag.attrs.items()}
    tag_name = tag.name.lower()

    if tag_name in ['textarea', 'input']:
        score = 0
        if 'prompt' in attrs.get('id', '') or 'prompt' in attrs.get('name', ''):
            score += 0.8
        if 'input' in attrs.get('class', []) or 'prompt' in attrs.get('class', []):
            score += 0.5
        if 'text' in attrs.get('type', '') or not attrs.get('type'):
            score += 0.3
        if score > 0:
            return {"role": "prompt_input", "confidence": min(1.0, score)}

    if tag_name == 'button':
        score = 0
        if 'submit' in text or 'send' in text or 'ask' in text:
            score += 0.8
        if 'submit' in attrs.get('type', '') or 'btn' in attrs.get('class', []):
            score += 0.5
        if 'submit' in attrs.get('id', '') or 'submit' in attrs.get('class', []):
            score += 0.4
        if score > 0:
            return {"role": "submit_button", "confidence": min(1.0, score)}

    if tag_name in ['div', 'p', 'span']:
        score = 0
        if len(text) > 20:
            score += 0.6
        if 'response' in attrs.get('class', []) or 'output' in attrs.get('class', []):
            score += 0.5
        if 'content' in attrs.get('id', '') or 'result' in attrs.get('id', ''):
            score += 0.4
        if score > 0:
            return {"role": "response_output", "confidence": min(1.0, score)}

    return {"role": None, "confidence": 0.0}

def _get_agent_suggestions(url, html, elements, model):
    agent = get_ai_adapter("LOCAL_DEEPSEEK", model=model)
    top_elements = sorted(elements, key=lambda x: x["candidate_role"]["confidence"], reverse=True)[:5]
    prompt = (
        f"Analyze this HTML snippet from {url}:\n\n{html[:1000]}\n\n"
        f"Here are the top detected elements:\n{json.dumps(top_elements, indent=2)}\n\n"
        "Suggest the best candidates for:\n"
        "- Prompt input (where to enter text)\n"
        "- Submit button (to send the prompt)\n"
        "- Response output (where the answer appears)\n"
        "Provide selectors and reasoning in JSON format."
    )
    try:
        logger.info("Sending prompt to agent")
        response = agent.delegate(prompt)
        logger.info(f"Agent suggestions: {response}")
        return {"raw_response": response}
    except Exception as e:
        logger.error(f"Agent analysis failed: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Discover DOM elements from a webpage with agent suggestions.",
        epilog="Example: python -m grok_local.dom_discovery --url https://grok.com --html-dir grok_chat_files --output grok_elements.json --model deepseek-r1 --info"
    )
    parser.add_argument("--url", required=True, help="Target URL to analyze")
    parser.add_argument("--html-dir", help="Directory containing saved HTML (e.g., Brave Save Page As)")
    parser.add_argument("--output", default="elements.json", help="Output JSON file")
    parser.add_argument("--browser", action="store_true", help="Use browser for dynamic DOM if fetching")
    parser.add_argument("--force", action="store_true", help="Force fetch even if HTML exists")
    parser.add_argument("--model", default="deepseek-r1", help="Local Ollama model (e.g., deepseek-r1, llama3.2)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.info:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    discover_dom(args.url, args.output, html_dir=args.html_dir, use_browser=args.browser, force=args.force, model=args.model)
