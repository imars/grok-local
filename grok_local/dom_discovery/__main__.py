#!/usr/bin/env python3
# grok_local/dom_discovery/__main__.py
import argparse
import logging
from grok_local.config import logger
from grok_local.dom_discovery import discover_dom

if __name__ == "__main__":
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
