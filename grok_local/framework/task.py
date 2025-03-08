from pydantic import BaseModel

class Task(BaseModel):
    description: str
    input_data: str = ""
    agent_role: str = "developer"
