import requests
import sys
import os
from .config import OLLAMA_URL, PROJECTS_DIR
from .logging import log_conversation
from .script_runner import debug_script
from ..commands import git_commands, file_commands, checkpoint_commands, bridge_commands, misc_commands
from ..framework.orchestrator import Orchestrator

def assess_complexity(command, debug=False):
    command = command.lower()
    cmd_length = len(command)
    simple_keywords = ["factorial", "list", "add", "reverse"]
    moderate_keywords = ["game", "clone", "pygame", "script"]
    advanced_keywords = ["3d", "universe", "persistent", "trade", "avatar"]
    
    if any(keyword in command for keyword in simple_keywords) and cmd_length < 50:
        complexity = "simple"
    elif any(keyword in command for keyword in moderate_keywords) or (50 <= cmd_length <= 150):
        complexity = "moderate"
    elif any(keyword in command for keyword in advanced_keywords) or cmd_length > 150:
        complexity = "advanced"
    else:
        complexity = "moderate"  # Default for ambiguous cases
    
    if debug:
        print(f"Debug: Assessed complexity: {complexity} for command: {command}", file=sys.stderr)
    return complexity

def execute_command(command, git_interface, ai_adapter, use_git=True, model=None, debug=False):
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
        complexity = assess_complexity(command, debug)
        orchestrator = Orchestrator()
        code, result = orchestrator.run_task(command, debug=debug, model=model)
        project_dir = os.path.join(PROJECTS_DIR, "output")
        os.makedirs(project_dir, exist_ok=True)
        script_path = os.path.join(project_dir, "output.py")
        with open(script_path, "w") as f:
            f.write(code)
        return f"{code}\nSaved code to '{script_path}'!\nDebug result: {result}"
