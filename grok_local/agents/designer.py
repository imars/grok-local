from .base_agent import BaseAgent
from ..framework.task import Task

class DesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__("llama3.2:latest")  # Lighter model for creative tasks

    def run(self, task: Task, memory):
        code = task.description.split("Refine code visually:")[1].strip()
        context = memory.retrieve(f"design:{code}") or ""
        prompt = f"Refine this code with visual improvements:\nCode:\n```python\n{code}\n```\nContext: {context}\nReturn only refined code in ```python\n<code>\n``` format."
        response = self._call_model(prompt)
        refined_code = response.split("```python")[1].split("```")[0].strip()
        memory.store(f"design:{code}", refined_code)
        return refined_code
