import requests
from .commands import git_commands, file_commands, checkpoint_commands, misc_commands

OLLAMA_URL = "http://localhost:11434/api/generate"

def execute_command(command, git_interface, ai_adapter, use_git=True):
    """Execute a command via the local agent's tools, with Ollama inference using llama3.2:latest by default."""
    command = command.strip().lower()
    
    # Restricted commands: no external calls unless whitelisted
    restricted = ["curl", "wget", "http"]
    if any(r in command for r in restricted):
        return "I can't perform direct external operations like that. Try 'grok <command>' for bridge assistance or specify a local command."

    # Route to existing command handlers
    if command.startswith("git "):
        return git_commands.git_command(command, git_interface)
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
        # Determine model based on command complexity
        model = "llama3.2:latest"  # Lightweight default
        if command.startswith("heavy "):
            model = "deepseek-r1:8b"
            command = command[6:].strip()
        
        # Try Ollama for local inference
        try:
            payload = {
                "model": model,
                "prompt": (
                    f"Act as Grok-Local, a CLI agent built by xAI. Respond to this command or query: '{command}'. "
                    f"You have tools: 'git <command>' for Git ops, 'create file <name>', 'read file <name>', "
                    f"'write <name> <content>', 'append <name> <content>', 'delete file <name>' for file ops, "
                    f"'checkpoint <msg>' to save progress, 'list checkpoints' to see saved points, "
                    f"'what time is it' for current time, 'version' for agent version, 'clean repo' to reset Git, "
                    f"'list files' for dir listing. No external calls (e.g., weather) unless escalated with 'grok <command>'. "
                    f"Use 'what time is it' tool for time queries and return a concise, friendly response."
                ),
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=10)
            if resp.status_code == 200:
                response = resp.json().get("response", "I processed your request, but got no clear answer.")
                # Post-process to insert real time if placeholder present
                if "[insert current time]" in response:
                    time_response = misc_commands.misc_command("what time is it", ai_adapter, git_interface)
                    response = response.replace("[insert current time]", time_response.split("is ")[-1])
                return response
            else:
                print(f"Debug: Ollama failed with {resp.status_code} - {resp.text}")
        except requests.RequestException as e:
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
