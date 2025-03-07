import requests
import os
import sys
import subprocess
from datetime import datetime
from .commands import git_commands, file_commands, checkpoint_commands, bridge_commands, misc_commands

OLLAMA_URL = "http://localhost:11434/api/generate"
PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent_conversations.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log_conversation(message):
    """Log agent conversation to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def debug_script(script_path, debug=False):
    """Run a Python script and return its output or error trace."""
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout
            if debug:
                print(f"Debug: Script ran successfully: {output}", file=sys.stderr)
            log_conversation(f"Debug script {script_path}: Success - {output}")
            return output
        else:
            error = result.stderr
            if debug:
                print(f"Debug: Script failed: {error}", file=sys.stderr)
            log_conversation(f"Debug script {script_path}: Error - {error}")
            return f"Error: {error}"
    except subprocess.TimeoutExpired:
        error = "Error: Script execution timed out after 30s"
        if debug:
            print(f"Debug: {error}", file=sys.stderr)
        log_conversation(f"Debug script {script_path}: {error}")
        return error
    except Exception as e:
        error = f"Error: Failed to run script: {str(e)}"
        log_conversation(f"Debug script {script_path}: {error}")
        return error

def execute_command(command, git_interface, ai_adapter, use_git=True, model=None, debug=False):
    """Execute a command via the local agent's tools, with hybrid Ollama inference."""
    command = command.strip().lower()

    restricted = ["curl", "wget", "http"]
    if any(r in command for r in restricted):
        return "I can't perform direct external operations like that. Try 'grok <command>' for bridge assistance or specify a local command."

    if command.startswith("git "):
        return git_commands.handle_git_command(command, git_interface)
    elif command.startswith(("create file ", "read file ", "write ", "append ", "delete file ")):
        return file_commands.file_command(command)
    elif command.startswith("checkpoint "):
        return checkpoint_commands.checkpoint_command(command, git_interface, use_git)
    elif command == "list checkpoints":
        return checkpoint_commands.list_checkpoints_command(command)
    elif command.startswith("grok "):
        return bridge_commands.bridge_command(command, ai_adapter)
    elif command in ["what time is it", "version", "clean repo", "list files"] or \
         command.startswith(("create spaceship fuel script", "create x login stub")):
        return misc_commands.misc_command(command, ai_adapter, git_interface)
    elif command.startswith("debug script "):
        script_path = command.split("debug script ", 1)[1].strip()
        return debug_script(script_path, debug)
    else:
        complexity = "complex"  # Skip complexity check
        if debug:
            print("Debug: Skipping complexity check, assuming 'complex'", file=sys.stderr)

        if model:
            selected_model = model
        elif complexity == "complex":
            selected_model = "deepseek-r1:8b"
        else:
            cmd_length = len(command)
            coding_keywords = ["clone", "game", "code", "build"]
            if any(keyword in command for keyword in coding_keywords):
                selected_model = "deepseek-r1:8b"
                if debug:
                    print("Debug: Coding keywords detected, using 'deepseek-r1:8b'", file=sys.stderr)
            elif cmd_length < 50:
                selected_model = "llama3.2:latest"
            elif cmd_length > 200:
                selected_model = "deepseek-r1:8b"
            else:
                selected_model = "llama3.2:latest"

        if debug:
            print(f"Debug: Selected model: {selected_model}", file=sys.stderr)
            print(f"Debug: Processing command: {command}", file=sys.stderr)

        try:
            payload = {
                "model": selected_model,
                "prompt": (
                    f"Act as Grok-Local, a CLI agent. Respond to this command: '{command}'. "
                    f"You have tools: 'git <command>', 'create file <name>', 'checkpoint <msg>', 'debug script <path>'. "
                    f"For coding tasks, generate complete, runnable Python code in ```python\n<code>\n``` and save to 'projects/<project_name>/'. "
                    f"If debugging, run the script with 'debug script <path>' and refine based on output/errors. Return a concise response."
                ),
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=900)  # Increased to 900s
            if resp.status_code == 200:
                response = resp.json().get("response", "No clear answer.")
                log_conversation(f"Command: {command}\nResponse: {response}")
                if "```python" in response and "asteroids" in command.lower():
                    code_block = response.split("```python")[1].split("```")[0].strip()
                    project_dir = os.path.join(PROJECTS_DIR, "asteroids")
                    os.makedirs(project_dir, exist_ok=True)
                    script_path = os.path.join(project_dir, "asteroids.py")
                    with open(script_path, "w") as f:
                        f.write(code_block)
                    response += f"\nSaved game code to '{script_path}'!"
                    debug_result = debug_script(script_path, debug)
                    response += f"\nDebug result: {debug_result}"
                return response
            else:
                error = "Failed to process with local inference. Try 'grok <command>' to escalate."
                log_conversation(f"Command: {command}\nError: {error}")
                return error
        except requests.RequestException as e:
            error = f"Ollama not running or timed out: {str(e)}. Try 'grok <command>' to escalate."
            log_conversation(f"Command: {command}\nError: {error}")
            return error
