import os

OLLAMA_URL = "http://localhost:11434/api/generate"
PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "..", "projects")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent_conversations.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)
