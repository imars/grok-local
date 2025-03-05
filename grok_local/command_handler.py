import re
import requests
import time
import subprocess
import uuid
from .commands import git_commands, file_commands, send_to_grok, checkpoint_commands, misc_commands
from .tools import execute_command

BRIDGE_URL = "http://0.0.0.0:5000"
BRIDGE_PROCESS = None

def start_bridge():
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS is None or BRIDGE_PROCESS.poll() is not None:
        BRIDGE_PROCESS = subprocess.Popen(["python", "grok_local/grok_bridge.py"])
        print("Started grok_bridge at http://0.0.0.0:5000")
        time.sleep(2)

def ask_local(command, ai_adapter, git_interface, debug=False, use_git=True, direct=False, model=None):
    command = command.strip()
    if debug:
        print(f"Debug: Processing command: {command}")

    # Handle bridge commands explicitly
    if re.match(r'^grok\s+', command):
        start_bridge()
        return send_to_grok(f"send to grok {command[5:]}", ai_adapter)

    if direct:
        # Direct execution mode with local inference fallback
        if re.match(r'^git\s+', command):
            return git_commands.git_command(command, git_interface)
        elif re.match(r'^(create|read|write|append|delete)\s+file\s+', command):
            return file_commands.file_command(command)
        elif re.match(r'^checkpoint\s+', command):
            return checkpoint_commands.checkpoint_command(command, git_interface, use_git)
        elif command == "list checkpoints":
            return checkpoint_commands.list_checkpoints_command(command)
        elif re.match(r'^(what time is it|version|x login|clean repo|list files|create spaceship fuel script|create x login stub)', command.lower()):
            return misc_commands.misc_command(command, ai_adapter, git_interface)
        elif re.match(r'^infer\s+', command):
            start_bridge()
            req_id = str(uuid.uuid4())
            sub_command = command[6:].strip()
            payload = {
                "input": (
                    f"Execute this command with your tool: '{sub_command}'. "
                    f"Tool: execute_command(command) - runs local commands (git, checkpoint, etc.) and returns results. "
                    f"Restrictions: no external calls (e.g., curl, wget) unless whitelisted. "
                    f"Respond with the tool's output or explain why you can't proceed."
                ),
                "id": req_id
            }
            if debug:
                print(f"Debug: Sending to bridge: {payload}")
            try:
                resp = requests.post(f"{BRIDGE_URL}/channel", json=payload, timeout=5)
                if debug:
                    print(f"Debug: POST response: {resp.status_code} - {resp.text}")
                if resp.status_code != 200:
                    return f"Error sending to bridge: {resp.text}"
                max_attempts, delay = 10, 2
                for attempt in range(max_attempts):
                    resp = requests.get(f"{BRIDGE_URL}/get-response", params={"id": req_id}, timeout=5)
                    if debug:
                        print(f"Debug: GET attempt {attempt + 1}: {resp.status_code} - {resp.text}")
                    if resp.status_code == 200:
                        return resp.text
                    elif resp.status_code != 404:
                        return f"Error fetching inference: {resp.text}"
                    time.sleep(delay)
                return "No inference response from agent within timeout"
            except requests.RequestException as e:
                return f"Error connecting to bridge: {e}"
        else:
            return execute_command(command, git_interface, ai_adapter, use_git, model=model)
    else:
        # Inference mode: use local agent directly
        return execute_command(command, git_interface, ai_adapter, use_git, model=model)
