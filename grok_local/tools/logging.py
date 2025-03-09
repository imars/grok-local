import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "grok_local.log")

def log_conversation(message):
    """Log a message to the specified log file with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to log message: {str(e)}", file=sys.stderr)
