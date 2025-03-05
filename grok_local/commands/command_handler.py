import re
import requests
import time
import subprocess
from .commands import git_commands, file_commands, bridge_commands, checkpoint_commands, misc_commands

BRIDGE_URL = "http://0.0.0.0:5000"
BRIDGE_PROCESS = None

def start_bridge():
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS is None or BRIDGE_PROCESS.poll() is not None:
        BRIDGE_PROCESS = subprocess.Popen(["python", "grok_local/grok_bridge.py"])
        print("Started grok_bridge at http://0.0.0.0:5000")
        time.sleep(2)

def ask_local(command, ai_adapter, git_interface, debug=False, use_git=True):
    command = command.strip()
    if debug:
        print(f"Debug: Processing command: {command}")

    if re.match(r'^git\s+', command):
        return git_commands.git_command(command, git_interface)
    elif re.match(r'^(create|read|write|append|delete)\s+file\s+', command):
        return file_commands.file_command(command)
    elif re.match(r'^send\s+to\s+grok\s+', command):
        start_bridge()
        return bridge_commands.send_to_grok(command, ai_adapter)
    elif re.match(r'^checkpoint\s+', command):
        return checkpoint_commands.checkpoint_command(command, git_interface, use_git)
    elif command == "list checkpoints":
        return checkpoint_commands.list_checkpoints_command(command)
    elif re.match(r'^(what time is it|version|x login|clean repo|list files|create spaceship fuel script|create x login stub)', command.lower()):
        return misc_commands.misc_command(command, ai_adapter, git_interface)
    else:
        # Inference fallback: send unknown command to Grok via bridge
        start_bridge()
        req_id = str(uuid.uuid4())
        payload = {"input": f"Unknown command: {command}. Please interpret and respond.", "id": req_id}
        try:
            resp = requests.post(f"{BRIDGE_URL}/channel", json=payload, timeout=5)
            if resp.status_code != 200:
                return f"Error sending to bridge: {resp.text}"
            max_attempts, delay = 10, 2
            for attempt in range(max_attempts):
                resp = requests.get(f"{BRIDGE_URL}/get-response", params={"id": req_id}, timeout=5)
                if resp.status_code == 200:
                    return f"Grok inference: {resp.text}"
                elif resp.status_code != 404:
                    return f"Error fetching inference: {resp.text}"
                time.sleep(delay)
            return "No inference response from Grok within timeout"
        except requests.RequestException as e:
            return f"Error connecting to bridge for inference: {e}"

