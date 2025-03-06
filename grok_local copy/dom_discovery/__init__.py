#!/usr/bin/env python3
# grok_local/dom_discovery/__init__.py
import os
import json  # Added missing import
import logging
from grok_local.config import logger
from .ollama_manager import ensure_ollama_running
from .html_fetcher import fetch_static, fetch_dynamic
from .element_parser import parse_elements
from .agent_analyzer import get_agent_suggestions

def discover_dom(url, output_json, html_dir=None, use_browser=False, force=False, model="deepseek-r1", retries=3):
    """Discover DOM elements from a directory or URL, with agent-suggested candidates."""
    elements = []
    html = None
    html_file = os.path.join(html_dir, "saved_resource.html") if html_dir else None

    if html_file and os.path.exists(html_file) and not force:
        logger.info(f"Using existing HTML file: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        if use_browser:
            html = fetch_dynamic(url, retries)
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

    elements = parse_elements(html)
    logger.info(f"Found {len(elements)} elements")

    if not ensure_ollama_running(model):
        logger.error(f"Could not start Ollama with model {model}")
        return

    agent_suggestions = get_agent_suggestions(url, html, elements, model)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"url": url, "elements": elements, "agent_suggestions": agent_suggestions}, f, indent=2)
    logger.info(f"DOM elements and agent suggestions saved to {output_json}")
