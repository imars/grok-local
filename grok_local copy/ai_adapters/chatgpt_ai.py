# grok_local/ai_adapters/chatgpt_ai.py
from abc import ABC, abstractmethod
import requests
import logging
from grok_local.config import logger, CHATGPT_API_KEY

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

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
