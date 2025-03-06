import requests
from .commands import git_commands, file_commands, checkpoint_commands, misc_commands

OLLAMA_URL = "http://localhost:11434/api/generate"

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
    elif command in ["what time is it", "version", "clean repo", "list files"] or \
         command.startswith(("create spaceship fuel script", "create x login stub")):
        return misc_commands.misc_command(command, ai_adapter, git_interface)
    else:
        # Check for Git summary requests
        git_summary_keywords = ["summarize", "changes", "log", "recent"]
        if any(keyword in command for keyword in git_summary_keywords) and ("repo" in command or "repository" in command):
            # Use handle_git_command with a concise log request
            git_log = git_commands.handle_git_command("git log 3", git_interface)  # Default to last 3 commits
            if debug:
                print(f"Debug: Raw git log output: {git_log}")
            try:
                payload = {
                    "model": "llama3.2:latest",
                    "prompt": (
                        f"Act as Grok-Local, a CLI agent built by xAI. The user asked: '{command}'. "
                        f"Here’s the real Git log output for the last 3 commits:\n{git_log}\n"
                        f"Summarize this Git log data concisely and truthfully—do not invent commits or details. "
                        f"Return a friendly response with the summary."
                    ),
                    "stream": False
                }
                resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
                if resp.status_code == 200:
                    return resp.json().get("response", "I processed the Git log, but got no clear summary.")
                else:
                    if debug:
                        print(f"Debug: Ollama failed with {resp.status_code} - {resp.text}")
                    return f"Got Git log:\n{git_log}\nBut couldn’t summarize it with Ollama."
            except requests.RequestException as e:
                if debug:
                    print(f"Debug: Ollama not running or failed for Git summary: {e}")
                return f"Got Git log:\n{git_log}\nBut Ollama isn’t available to summarize it."

        # Model selection: override or hybrid auto-selection
        if model:
            selected_model = model
        else:
            cmd_length = len(command)
            if cmd_length < 50:  # Short: lightweight model
                selected_model = "llama3.2:latest"
            elif cmd_length > 200:  # Long: reasoning model
                selected_model = "deepseek-r1:8b"
            else:  # Medium: assess complexity with lightweight model
                try:
                    payload = {
                        "model": "llama3.2:latest",
                        "prompt": (
                            f"Assess the complexity of this command: '{command}'. "
                            f"Respond with 'simple' for basic tasks or 'complex' for reasoning-heavy tasks."
                        ),
                        "stream": False
                    }
                    resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
                    if resp.status_code == 200:
                        complexity = resp.json().get("response", "simple").strip().lower()
                        selected_model = "deepseek-r1:8b" if complexity == "complex" else "llama3.2:latest"
                    else:
                        if debug:
                            print(f"Debug: Ollama complexity check failed with {resp.status_code} - {resp.text}")
                        selected_model = "llama3.2:latest"
                except requests.RequestException as e:
                    if debug:
                        print(f"Debug: Ollama complexity check not running or failed: {e}")
                    selected_model = "llama3.2:latest"

        # Execute with selected model
        try:
            payload = {
                "model": selected_model,
                "prompt": (
                    f"Act as Grok-Local, a CLI agent built by xAI. Respond to this command or query: '{command}'. "
                    f"You have tools: 'git <command>' for Git ops, 'create file <name>', 'read file <name>', "
                    f"'write <name> <content>', 'append <name> <content>', 'delete file <name>' for file ops, "
                    f"'checkpoint <msg>' to save progress, 'list checkpoints' to see saved points, "
                    f"'what time is it' for current time, 'version' for agent version, 'clean repo' to reset Git, "
                    f"'list files' for dir listing. No external calls (e.g., weather) unless escalated with 'grok <command>'. "
                    f"Use 'what time is it' tool for time queries. Return a concise, friendly response."
                ),
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
            if resp.status_code == 200:
                response = resp.json().get("response", "I processed your request, but got no clear answer.")
                if "[insert current time]" in response:
                    time_response = misc_commands.misc_command("what time is it", ai_adapter, git_interface)
                    response = response.replace("[insert current time]", time_response.split("is ")[-1])
                return response
            else:
                if debug:
                    print(f"Debug: Ollama failed with {resp.status_code} - {resp.text}")
        except requests.RequestException as e:
            if debug:
                print(f"Debug: Ollama not running or failed: {e}")
        
        # Fallback to static responses
        if "weather" in command:
            return "I don’t have weather data locally. Try 'grok \"get weather\"' to escalate this to the bridge."
        elif "time" in command and "what" not in command:
            return misc_commands.misc_command("what time is it", ai_adapter, git_interface)
        elif "how are you" in command or "how's it going" in command:
            return "I’m doing great, thanks for asking! How can I assist you today?"
        elif "hello" in command or "hi" in command:
            return "Hi there! I’m Grok-Local, ready to help with your tasks."
        else:
            return f"Command '{command}' not recognized by local tools. Try 'grok <command>' for bridge inference or use a specific local command like 'checkpoint <msg>'."
