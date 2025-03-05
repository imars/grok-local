#!/usr/bin/env python3
# grok_local/command_handler.py
import logging
from .commands import git_commands, file_commands, bridge_commands, checkpoint_commands, misc_commands

logger = logging.getLogger()

def process_multi_command(request, ai_adapter, git_interface, debug=False):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd, ai_adapter, git_interface, debug)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def ask_local(request, ai_adapter, git_interface, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.debug(f"Debug processing: {request}")
    logger.info(f"Processing command: {request}")

    if "&&" in request:
        return process_multi_command(request, ai_adapter, git_interface, debug)

    req_lower = request.lower()
    # Route to appropriate module
    if req_lower.startswith("git "):
        return git_commands.handle_git_command(request, git_interface)
    elif any(req_lower.startswith(cmd) for cmd in ["create file ", "delete file ", "move file ", "copy file ", "rename file ", "read file ", "write "]):
        return file_commands.handle_file_command(request)
    elif req_lower.startswith("send to grok ") or req_lower.startswith("grok "):
        return bridge_commands.handle_bridge_command(request, ai_adapter)
    elif req_lower.startswith("checkpoint ") or req_lower == "list checkpoints":
        return checkpoint_commands.handle_checkpoint_command(request, git_interface)
    elif req_lower in ["what time is it", "ask what time is it", "version", "clean repo", "list files", "create spaceship fuel script", "create x login stub"]:
        return misc_commands.handle_misc_command(request, ai_adapter, git_interface)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"
