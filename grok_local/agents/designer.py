from .base_agent import BaseAgent
from ..framework.task import Task
from ..tools.logging import log_conversation

class DesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__("llama3.2:latest")  # Lighter model for creative tasks

    def run(self, task: Task, memory):
        code = task.description.split("Refine code visually:")[1].strip()
        context = memory.retrieve(f"design:{code}") or ""
        prompt = f"Refine this code with visual improvements:\nCode:\n\nContext: {context}\nReturn only refined code in  format."
        response = self._call_model(prompt)
        refined_code = response.split("")[0].strip()
        memory.store(f"design:{code}", refined_code)
        log_conversation(f"Designer: Refined code for {task.description}")
        return refined_code
