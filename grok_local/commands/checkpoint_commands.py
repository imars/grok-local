import json
import os
import uuid
from datetime import datetime
from grok_checkpoint import save_checkpoint

def checkpoint_command(command, git_interface, use_git=True):
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        return "Error: Checkpoint requires a message (e.g., 'checkpoint \"Update\"')"
    
    message = parts[1].strip()
    if message.startswith('"') and message.endswith('"'):
        message = message[1:-1]
    
    chat_id = str(uuid.uuid4())
    checkpoint_data = {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "chat_id": chat_id,
        "group": "default"
    }
    filepath = os.path.join("checkpoints", "checkpoint.json")
    os.makedirs("checkpoints", exist_ok=True)
    save_checkpoint(checkpoint_data, filepath)
    report = f"Checkpoint saved: \"{message}\" to {filepath}"
    
    if use_git and git_interface:
        commit_message = f"Checkpoint: \"{message}\" (Chat: {chat_id}, Group: default)"
        result = git_interface.commit_and_push(commit_message)  # Fixed: only message
        report += f"\n{result}"
    
    return report

def list_checkpoints_command(command):
    filepath = os.path.join("checkpoints", "checkpoint.json")
    if not os.path.exists(filepath):
        return "No checkpoints found."
    
    with open(filepath, 'r') as f:
        checkpoints = json.load(f)
    
    if isinstance(checkpoints, list):
        return "\n".join([f"- {cp['timestamp']}: {cp['message']} (Chat: {cp['chat_id']})" for cp in checkpoints])
    else:
        return f"- {checkpoints['timestamp']}: {checkpoints['message']} (Chat: {checkpoints['chat_id']})"
