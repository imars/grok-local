# grok_local/ai_adapters/stub_ai.py
from abc import ABC, abstractmethod
import logging
from grok_local.config import logger

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
