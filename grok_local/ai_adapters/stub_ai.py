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
            return "```python\nprint('Stubbed spaceship fuel script')\n```"
        elif "x login stub" in request.lower():
            return "```python\nprint('Stubbed X login script')\n```"
        return "```python\nStubbed response\n```"
