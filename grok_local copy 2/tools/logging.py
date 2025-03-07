from datetime import datetime
from .config import LOG_FILE

def log_conversation(message):
    """Log agent conversation to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
