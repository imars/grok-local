from .base_agent import BaseAgent
from ..framework.task import Task
from ..tools.logging import log_conversation
from datetime import datetime
from ..ai_adapters.stub_ai import StubAI

class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__("deepseek-r1:8b")
        self.stub_ai = StubAI()

    def run(self, task: Task, memory):
        context = memory.retrieve(task.description) or ""
        prompt = f"Generate Python code for: {task.description}. Context: {context}\nReturn only code in ```python format, no explanations."
        log_conversation(f"Developer: Sending prompt at {datetime.now()}: {prompt}")
        response = self.stub_ai.delegate(prompt)
        log_conversation(f"Developer: Received response at {datetime.now()}: {response}")
        try:
            if "```python" in response:
                code = response.split("```python")[1].split("```")[0].strip()
            else:
                code = response.strip()
                log_conversation(f"Developer: Warning - No ```python block found, using raw response: {code}")
        except IndexError:
            code = response.strip()
            log_conversation(f"Developer: Error parsing code block, using raw response: {code}")
        memory.store(task.description, code)
        return code
