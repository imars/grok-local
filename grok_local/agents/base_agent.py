from abc import ABC, abstractmethod
import requests
from ..tools import OLLAMA_URL, log_conversation

class BaseAgent(ABC):
    def __init__(self, model="deepseek-r1:8b"):
        self.model = model

    def _call_model(self, prompt, timeout=600):
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()["response"]
            return f"Error: {resp.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    @abstractmethod
    def run(self, task, memory):
        pass
