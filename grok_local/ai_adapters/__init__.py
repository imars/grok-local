# grok_local/ai_adapters/__init__.py
from .stub_ai import StubAI
from .manual_ai import ManualAI
from .grok_browser_ai import GrokBrowserAI
from .chatgpt_ai import ChatGPTAI
from .deepseek_ai import DeepSeekAI
from .local_deepseek_ai import LocalDeepSeekAI

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
