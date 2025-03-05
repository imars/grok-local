# grok_local/commands/checkpoint_commands.py
import logging
from grok_checkpoint import save_checkpoint, list_checkpoints
from ..utils import report

logger = logging.getLogger(__name__)

def handle_checkpoint_command(request, git_interface):
    req_lower = request.lower()
    if req_lower == "list checkpoints":
        return report(list_checkpoints())
    elif req_lower.startswith("checkpoint "):
        description = request[10:].strip()
        if not description:
            return "Error: Checkpoint requires a description"
        parts = description.split(" --file ")
        desc = parts[0].strip("'")
        filename = parts[1].split()[0].strip("'") if len(parts) > 1 else "checkpoint.json"
        content = None
        chat_url = None
        git_update = "--git" in description
        if git_update:
            desc = desc.replace(" --git", "").strip()

        params = " ".join(parts[1:]) if len(parts) > 1 else parts[0]
        if "with current x_poller.py content" in params:
            try:
                with open("x_poller.py", "r") as f:
                    content = f.read()
            except FileNotFoundError:
                logger.error("x_poller.py not found for checkpoint")
                return "Error: x_poller.py not found"
        for param in params.split():
            if param.startswith("chat_url="):
                chat_url = param.split("=", 1)[1].strip("'")

        return report(save_checkpoint(desc, git_interface, filename=filename, file_content=content, chat_url=chat_url, git_update=git_update))
    else:
        return f"Unknown checkpoint command: {request}"
