from .base_agent import BaseAgent
from ..framework.task import Task
from ..tools import debug_script, log_conversation
from datetime import datetime

class DebuggerAgent(BaseAgent):
    def __init__(self):
        super().__init__("deepseek-r1:8b")

    def run(self, task: Task, memory):
        log_conversation(f"Debugger: Received task at {datetime.now()}: {task.description}")
        code = task.description.split("Fix code:")[1].strip()
        error = task.input_data
        context = memory.retrieve(f"debug:{code}") or ""
        prompt = f"Fix this code given the error:\nCode:\n```python\n{code}\n```\nError: {error}\nContext: {context}\nReturn only fixed code in ```python\n<code>\n``` format, no explanations."
        log_conversation(f"Debugger: Starting model call at {datetime.now()} with prompt length: {len(prompt)}")
        response = self._call_model(prompt)
        log_conversation(f"Debugger: Model call completed at {datetime.now()}")
        try:
            fixed_code = response.split("```python")[1].split("```")[0].strip()
        except IndexError:
            fixed_code = response  # Fallback if no code block
        memory.store(f"debug:{code}", f"Fixed: {fixed_code}\nError: {error}")
        log_conversation(f"Debugger: Task completed at {datetime.now()}, result: {fixed_code}")
        return fixed_code
