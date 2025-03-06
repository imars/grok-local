import json
import os
import uuid
from datetime import datetime
from grok_checkpoint import save_checkpoint

def checkpoint_command(command, git_interface, use_git=True, chat_address=None):
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        return "Error: Checkpoint requires a message (e.g., 'checkpoint \"Update\"')"

    message = parts[1].strip()
    if message.startswith('"') and message.endswith('"'):
        message = message[1:-1]

    chat_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    checkpoint_data = {
        "description": {
            "message": message,
            "timestamp": timestamp,
            "chat_id": chat_id,
            "group": "default"
        },
        "timestamp": timestamp,
        "files": ["grok_bootstrap.py"],  # Default file, adjust as needed
        "current_task": "",  # Could be parameterized in future
        "chat_address": chat_address if chat_address else str(uuid.uuid4()),
        "chat_group": "default"
    }
    filepath = os.path.join("checkpoints", "checkpoint.json")
    os.makedirs("checkpoints", exist_ok=True)

    # Load existing checkpoints if file exists, append new entry
    existing_checkpoints = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                existing_checkpoints = json.load(f)
            if not isinstance(existing_checkpoints, list):
                existing_checkpoints = [existing_checkpoints]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load existing checkpoints: {e}", file=sys.stderr)

    existing_checkpoints.append(checkpoint_data)
    with open(filepath, 'w') as f:
        json.dump(existing_checkpoints, f, indent=4)

    report = f"Checkpoint saved: \"{message}\" to {filepath}"

    if use_git and git_interface:
        commit_message = f"Checkpoint: \"{message}\" (Chat: {chat_id}, Group: default)"
        result = git_interface.commit_and_push(commit_message)
        report += f"\n{result}"

    return report

def list_checkpoints_command(command):
    filepath = os.path.join("checkpoints", "checkpoint.json")
    if not os.path.exists(filepath):
        return "No checkpoints found."

    with open(filepath, 'r') as f:
        checkpoints = json.load(f)

    if isinstance(checkpoints, list):
        return "\n".join([f"- {cp['description']['timestamp']}: {cp['description']['message']} (Chat: {cp['description']['chat_id']})" for cp in checkpoints])
    else:
        return f"- {checkpoints['description']['timestamp']}: {checkpoints['description']['message']} (Chat: {checkpoints['description']['chat_id']})"
