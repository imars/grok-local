from .base_agent import BaseAgent
from ..framework.task import Task
from ..tools.logging import log_conversation
from datetime import datetime

class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__("deepseek-r1:8b")

    def run(self, task: Task, memory):
        context = memory.retrieve(task.description) or ""
        prompt = f"Generate Python code for: {task.description}. Context: {context}\nReturn only code in  format, no explanations."
        log_conversation(f"Developer: Sending prompt at {datetime.now()}: {prompt}")
        response = self._call_model(prompt)
        log_conversation(f"Developer: Received response at {datetime.now()}: {response}")
        try:
            code = response.split("")[0].strip()
        except IndexError:
            code = response.strip()  # Fallback: use raw response if no block
            log_conversation(f"Developer: Warning - No code block found, using raw response: {code}")
        memory.store(task.description, code)
        return code
