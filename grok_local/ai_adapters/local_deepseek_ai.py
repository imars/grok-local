# grok_local/ai_adapters/local_deepseek_ai.py
from abc import ABC, abstractmethod
import requests
import time
import logging
from grok_local.config import logger

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

class LocalDeepSeekAI(AIAdapter):
    def __init__(self, model="deepseek-r1"):
        self.model = model
        logger.info(f"Warming up {self.model}")
        self.delegate("Warm-up: Analyze a simple HTML snippet for input and button elements.")

    def delegate(self, request):
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model,
                "prompt": request,
                "stream": False
            }
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=600)
            end_time = time.time()
            logger.info(f"Local {self.model} took {end_time - start_time:.2f} seconds")
            response.raise_for_status()
            result = response.json()["response"]
            logger.info(f"Local {self.model} response: {result}")
            return result
        except Exception as e:
            logger.error(f"Local {self.model} error: {str(e)}")
            return f"Error with local {self.model}: {str(e)}"
