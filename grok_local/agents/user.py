from .base_agent import BaseAgent
from ..framework.task import Task

class UserAgent(BaseAgent):
    def __init__(self):
        super().__init__(None)  # No model needed

    def run(self, task: Task, memory):
        code = task.description.split("Review code:")[1].strip()
        print(f"Current code:\n{code}")
        user_input = input("Review code—any changes? (Enter to accept, or suggest edits): ")
        if user_input:
            memory.store(f"user:{code}", user_input)
            return f"{code}\n# User edit: {user_input}"
        return code
