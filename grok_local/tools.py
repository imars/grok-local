import requests
import os
import sys
from .commands import git_commands, file_commands, checkpoint_commands, bridge_commands, misc_commands

OLLAMA_URL = "http://localhost:11434/api/generate"
PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")

def execute_command(command, git_interface, ai_adapter, use_git=True, model=None, debug=False):
    """Execute a command via the local agent's tools, with hybrid Ollama inference."""
    command = command.strip().lower()

    # Restricted commands: no external calls unless whitelisted
    restricted = ["curl", "wget", "http"]
    if any(r in command for r in restricted):
        return "I can't perform direct external operations like that. Try 'grok <command>' for bridge assistance or specify a local command."

    # Route to existing command handlers
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
    else:
        # Pre-check complexity for all commands
        try:
            payload = {
                "model": "llama3.2:latest",
                "prompt": f"Assess the complexity of this command: '{command}'. Respond with 'simple' for basic tasks or 'complex' for reasoning-heavy tasks.",
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
            if resp.status_code == 200:
                complexity = resp.json().get("response", "simple").strip().lower()
                if debug:
                    print(f"Debug: Command complexity assessed as '{complexity}'", file=sys.stderr)
            else:
                complexity = "simple"
        except requests.RequestException as e:
            complexity = "simple"
            if debug:
                print(f"Debug: Complexity check failed: {str(e)}, defaulting to 'simple'", file=sys.stderr)

        # Model selection: override, complexity, or keywords
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

        # Execute with selected model
        try:
            payload = {
                "model": selected_model,
                "prompt": (
                    f"Act as Grok-Local, a CLI agent. Respond to this command: '{command}'. "
                    f"You have tools: 'git <command>', 'create file <name>', 'checkpoint <msg>', etc. "
                    f"For coding tasks, generate complete Python code in ```python\n<code>\n``` and save to 'projects/<project_name>/'. "
                    f"Return a concise response."
                ),
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=300)  # Increased to 300s
            if resp.status_code == 200:
                response = resp.json().get("response", "No clear answer.")
                if "```python" in response and "asteroids" in command:
                    code_block = response.split("```python")[1].split("```")[0].strip()
                    project_dir = os.path.join(PROJECTS_DIR, "asteroids")
                    os.makedirs(project_dir, exist_ok=True)
                    with open(os.path.join(project_dir, "asteroids.py"), "w") as f:
                        f.write(code_block)
                    response += f"\nSaved game code to 'projects/asteroids/asteroids.py'!"
                return response
            else:
                return "Failed to process with local inference. Try 'grok <command>' to escalate."
        except requests.RequestException as e:
            return f"Ollama not running or timed out: {str(e)}. Try 'grok <command>' to escalate."
