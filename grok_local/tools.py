from .commands import git_commands, file_commands, checkpoint_commands, misc_commands

def execute_command(command, git_interface, ai_adapter, use_git=True):
    """Execute a command via the local agent's tools, with restrictions and conversational responses."""
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
        # Smarter local inference with conversational responses
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
