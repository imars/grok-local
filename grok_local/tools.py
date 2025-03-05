from .commands import git_commands, file_commands, checkpoint_commands, misc_commands

def execute_command(command, git_interface, ai_adapter, use_git=True):
    """Execute a command via the local agent's tools, with restrictions."""
    command = command.strip().lower()
    
    # Restricted commands: no external calls unless whitelisted
    restricted = ["curl", "wget", "http", "weather"]  # Example restrictions
    if any(r in command for r in restricted):
        return "I can't perform external operations like that. Use 'grok' for bigger tasks or specific local commands."

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
        return f"Command '{command}' not recognized by local tools."
