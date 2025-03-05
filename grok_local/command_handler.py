import re
import requests
import time
from .commands import git_commands, file_commands, bridge_commands, checkpoint_commands, misc_commands

BRIDGE_URL = "http://0.0.0.0:5000"

def ask_local(command, ai_adapter, git_interface, debug=False, use_git=True):
    command = command.strip()
    if debug:
        print(f"Debug: Processing command: {command}")

    if re.match(r'^git\s+', command):
        return git_commands.git_command(command, git_interface)
    elif re.match(r'^(create|read|write|append|delete)\s+file\s+', command):
        return file_commands.file_command(command)
    elif re.match(r'^send\s+to\s+grok\s+', command):
        return bridge_commands.send_to_grok(command, ai_adapter)
    elif re.match(r'^checkpoint\s+', command):
        return checkpoint_commands.checkpoint_command(command, git_interface, use_git)
    elif command == "list checkpoints":
        return checkpoint_commands.list_checkpoints_command(command)
    elif command == "what time is it":
        return misc_commands.time_command()
    elif command == "version":
        return misc_commands.version_command()
    elif command.startswith("x login "):
        return misc_commands.x_login_stub(command)
    else:
        return f"Unknown command: {command}"
