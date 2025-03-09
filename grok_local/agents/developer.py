from .base_agent import BaseAgent
from ..framework.task import Task
from ..tools.logging import log_conversation
from datetime import datetime

class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__("deepseek-r1:8b")

    def run(self, task: Task, memory):
        context = memory.retrieve(task.description) or ""
        prompt = f"Generate Python code for: {task.description}. Context: {context}\nReturn only code in ```python format, no explanations."
        log_conversation(f"Developer: Sending prompt at {datetime.now()}: {prompt}")
        response = self._call_model(prompt)
        log_conversation(f"Developer: Received response at {datetime.now()}: {response}")
        try:
            # Extract code between ```python and ```
            if "```python" in response:
                code = response.split("```python")[1].split("```")[0].strip()
            else:
                code = response.strip()  # Fallback: use raw response
                log_conversation(f"Developer: Warning - No ```python block found, using raw response: {code}")
        except IndexError:
            code = response.strip()  # Fallback on error
            log_conversation(f"Developer: Error parsing code block, using raw response: {code}")
        memory.store(task.description, code)
        return code
