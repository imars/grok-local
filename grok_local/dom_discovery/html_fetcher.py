# grok_local/dom_discovery/html_fetcher.py
import requests
import time
import logging
from grok_local.config import logger, BROWSER_BACKEND
from grok_local.browser_adapter import BrowserAdapter

def fetch_static(url):
    """Fetch HTML statically using requests."""
    try:
        logger.info(f"Fetching {url} statically")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Static DOM fetch failed: {str(e)}")
        return None

def fetch_dynamic(url, retries):
    """Fetch HTML dynamically using a browser."""
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
            return html
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                logger.error("All retries failed; falling back to static fetch")
                return fetch_static(url)
            time.sleep(2)
    return None
