# grok_local/dom_discovery/element_parser.py
from bs4 import BeautifulSoup
import logging
from grok_local.config import logger

def parse_elements(html):
    """Parse HTML for relevant DOM elements."""
    soup = BeautifulSoup(html, 'html.parser')
    logger.info("Parsing HTML with BeautifulSoup")
    elements = []
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
    return elements

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
