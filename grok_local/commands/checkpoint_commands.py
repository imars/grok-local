import json
import sys
from datetime import datetime
import uuid
import os

def checkpoint_command(command, git_interface=None, use_git=True):
    message = command.split("checkpoint ", 1)[1].strip("'\"")
    checkpoint_file = "checkpoints/checkpoint.json"
    os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
    chat_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    checkpoint = {
        "description": {
            "message": message,
            "timestamp": timestamp,
            "chat_id": chat_id,
            "group": "default"
        },
        "timestamp": timestamp,
        "files": [f"grok_local/projects/asteroids/asteroids.py"],  # Adjust as needed
        "current_task": "Building Asteroids game",
        "chat_address": chat_id,
        "chat_group": "default"
    }

    report = f"Checkpoint saved: \"{message}\" to {checkpoint_file}"

    try:
        with open(checkpoint_file, "r") as f:
            existing_checkpoints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load existing checkpoints: {e}", file=sys.stderr)
        existing_checkpoints = []

    if not isinstance(existing_checkpoints, list):
        print(f"Warning: Resetting malformed checkpoint file", file=sys.stderr)
        existing_checkpoints = []

    existing_checkpoints.append(checkpoint)

    with open(checkpoint_file, "w") as f:
        json.dump(existing_checkpoints, f, indent=4)

    if use_git and git_interface:
        commit_message = f"Checkpoint: \"{message}\" (Chat: {chat_id}, Group: default)"
        result = git_interface.commit_and_push(commit_message)
        report += f"\n{result}"

    return report

def list_checkpoints_command(command):
    checkpoint_file = "checkpoints/checkpoint.json"
    try:
        with open(checkpoint_file, "r") as f:
            checkpoints = json.load(f)
        if not checkpoints:
            return "No checkpoints found."
        return "\n".join([f"{cp['timestamp']}: {cp['description']['message']}" for cp in checkpoints])
    except FileNotFoundError:
        return "No checkpoints file found."
    except json.JSONDecodeError as e:
        return f"Error reading checkpoints: {e}"
