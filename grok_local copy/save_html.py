#!/usr/bin/env python3
# grok_local/save_html.py
import requests
from grok_local.config import logger

def save_html(url, output_file):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Saved HTML from {url} to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save HTML from {url}: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m grok_local.save_html <url> <output_file>")
        sys.exit(1)
    save_html(sys.argv[1], sys.argv[2])
