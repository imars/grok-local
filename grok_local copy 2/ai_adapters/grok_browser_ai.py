# grok_local/ai_adapters/grok_browser_ai.py
from abc import ABC, abstractmethod
import time
import logging
from grok_local.browser_adapter import BrowserAdapter
from grok_local.config import logger, BROWSER_BACKEND

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

class GrokBrowserAI(AIAdapter):
    def __init__(self):
        self.browser = BrowserAdapter(BROWSER_BACKEND)

    def delegate(self, request):
        try:
            logger.info("Navigating to grok.com home page")
            self.browser.goto("https://grok.com")
            time.sleep(5)
            logger.debug(f"Sending prompt: {request}")
            self.browser.fill(".question-input", request)
            self.browser.click(".submit-btn")
            time.sleep(5)
            response = self.browser.extract_text(".response-output")
            if not response or response.strip() == "":
                logger.warning("No response extracted from grok.com")
                return "No response received from grok.com"
            logger.info(f"Grok.com browser response to '{request}': {response}")
            return response
        except Exception as e:
            logger.error(f"Browser interaction error: {str(e)}")
            return f"Error with grok.com browser: {str(e)}"
        finally:
            self.browser.close()
