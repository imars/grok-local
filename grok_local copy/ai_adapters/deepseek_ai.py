# grok_local/ai_adapters/deepseek_ai.py
from abc import ABC, abstractmethod
import requests
import logging
from grok_local.config import logger, DEEPSEEK_API_KEY

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

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
