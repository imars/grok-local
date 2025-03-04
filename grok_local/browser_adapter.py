# grok_local/browser_adapter.py
import logging
from grok_local.config import logger

# Conditional imports for browser backends
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from browser_use import Browser
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False

class BrowserAdapter:
    def __init__(self, backend, headless=True):
        self.backend = backend
        self.driver = None
        self.headless = headless
        if backend == "SELENIUM" and SELENIUM_AVAILABLE:
            self.driver = webdriver.Chrome()
        elif backend == "PLAYWRIGHT" and PLAYWRIGHT_AVAILABLE:
            self.playwright = sync_playwright().start()
            self.driver = self.playwright.chromium.launch(headless=self.headless).new_page()
        elif backend == "BROWSER_USE" and BROWSER_USE_AVAILABLE:
            self.driver = Browser()
        else:
            logger.error(f"Unsupported or unavailable browser backend: {backend}")
            raise ValueError(f"Unsupported or unavailable browser backend: {backend}")

    def goto(self, url):
        logger.debug(f"Navigating to {url} with {self.backend}")
        if self.backend == "SELENIUM":
            self.driver.get(url)
        elif self.backend == "PLAYWRIGHT":
            self.driver.goto(url)
        elif self.backend == "BROWSER_USE":
            self.driver.goto(url)  # Assuming Browser supports goto

    def fill(self, selector, value):
        logger.debug(f"Filling {selector} with '{value}' using {self.backend}")
        if self.backend == "SELENIUM":
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(value)
        elif self.backend == "PLAYWRIGHT":
            self.driver.wait_for_selector(selector, timeout=10000)
            self.driver.fill(selector, value)
        elif self.backend == "BROWSER_USE":
            self.driver.fill(selector, value)

    def click(self, selector):
        logger.debug(f"Clicking {selector} with {self.backend}")
        if self.backend == "SELENIUM":
            self.driver.find_element(By.CSS_SELECTOR, selector).click()
        elif self.backend == "PLAYWRIGHT":
            self.driver.wait_for_selector(selector, timeout=10000)
            self.driver.click(selector)
        elif self.backend == "BROWSER_USE":
            self.driver.click(selector)

    def extract_text(self, selector):
        logger.debug(f"Extracting text from {selector} with {self.backend}")
        if self.backend == "SELENIUM":
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text
        elif self.backend == "PLAYWRIGHT":
            self.driver.wait_for_selector(selector, timeout=10000)
            return self.driver.locator(selector).inner_text()
        elif self.backend == "BROWSER_USE":
            return self.driver.extract_text(selector)

    def close(self):
        logger.debug(f"Closing browser with {self.backend}")
        if self.backend == "SELENIUM":
            self.driver.quit()
        elif self.backend == "PLAYWRIGHT":
            self.driver.close()
            self.playwright.stop()
        elif self.backend == "BROWSER_USE":
            self.driver.close()
