# grok_local/ai_adapters/manual_ai.py
from abc import ABC, abstractmethod
import logging
from grok_local.config import logger

class AIAdapter(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

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
