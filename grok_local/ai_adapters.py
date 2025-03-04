# grok_local/ai_adapters.py
from abc import ABC, abstractmethod
import os
import logging
import requests
import time
from grok_local.browser_adapter import BrowserAdapter
from grok_local.config import logger, BROWSER_BACKEND, CHATGPT_API_KEY, DEEPSEEK_API_KEY

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

class StubAI(AIAdapter):
    def delegate(self, request):
        logger.debug(f"Stubbed delegation for: {request}")
        if "spaceship fuel script" in request.lower():
            return "print('Stubbed spaceship fuel script')"
        elif "x login stub" in request.lower():
            return "print('Stubbed X login script')"
        return f"Stubbed response for: {request}"

class ManualAI(AIAdapter):
    def delegate(self, request):
        logger.info(f"Delegating manually: {request}")
        print(f"Request sent: {request}")
        print("Awaiting response... (Paste and press Ctrl+D or Ctrl+Z then Enter)")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            response = "\n".join(lines).strip()
        logger.info(f"Received response:\n{response}")
        return response

class GrokBrowserAI(AIAdapter):
    def __init__(self):
        self.browser = BrowserAdapter(BROWSER_BACKEND)

    def delegate(self, request):
        try:
            logger.info("Navigating to grok.com home page")
            self.browser.goto("https://grok.com")
            time.sleep(5)
            logger.debug(f"Sending prompt: {request}")
            self.browser.fill("#prompt", request)  # Placeholder
            self.browser.click("button.submit-btn")
            time.sleep(5)
            response = self.browser.extract_text("div.response-area")
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

class ChatGPTAI(AIAdapter):
    def delegate(self, request):
        if not CHATGPT_API_KEY:
            logger.error("CHATGPT_API_KEY not set")
            return "Error: ChatGPT API key missing"
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {CHATGPT_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": request}]}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            logger.info(f"ChatGPT response to '{request}': {result}")
            return result
        except Exception as e:
            logger.error(f"ChatGPT API error: {str(e)}")
            return f"Error with ChatGPT: {str(e)}"

class DeepSeekAI(AIAdapter):
    def delegate(self, request):
        if not DEEPSEEK_API_KEY:
            logger.error("DEEPSEEK_API_KEY not set")
            return "Error: DeepSeek API key missing"
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": request}]}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            logger.info(f"DeepSeek response to '{request}': {result}")
            return result
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return f"Error with DeepSeek: {str(e)}"

class LocalDeepSeekAI(AIAdapter):
    def __init__(self, model="deepseek-r1"):
        self.model = model
        # Warm-up call to ensure model is ready
        self.delegate("Warm-up prompt: Hello, are you ready?")

    def delegate(self, request):
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model,
                "prompt": request,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=600)  # Increased from 60 to 600
            response.raise_for_status()
            result = response.json()["response"]
            logger.info(f"Local {self.model} response: {result}")
            return result
        except Exception as e:
            logger.error(f"Local {self.model} error: {str(e)}")
            return f"Error with local {self.model}: {str(e)}"

def get_ai_adapter(backend=os.getenv("AI_BACKEND", "STUB"), model="deepseek-r1"):
    backends = {
        "STUB": StubAI,
        "MANUAL": ManualAI,
        "GROK_BROWSER": GrokBrowserAI,
        "CHATGPT": ChatGPTAI,
        "DEEPSEEK": DeepSeekAI,
        "LOCAL_DEEPSEEK": lambda: LocalDeepSeekAI(model)
    }
    if backend not in backends:
        logger.error(f"Unsupported AI backend: {backend}")
        raise ValueError(f"Unsupported AI backend: {backend}")
    return backends[backend]()
