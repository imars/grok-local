#!/usr/bin/env python3
# grok_bootstrap.py (Mar 05, 2025): Restarts dev chat sessions with context.
# Options: --dump (full file contents), --prompt (chat-ready summary), --most-recent (summary + recent files).

import argparse
import sys
import os
import datetime

# Critical files to include in prompt
CRITICAL_FILES = [
    "grok_local/__main__.py",
    "grok_local/command_handler.py",
    "grok_local/grok_bridge.py",
    "grok_local/commands/__init__.py",
    "grok_local/commands/git_commands.py",
    "grok_local/commands/file_commands.py",
    "grok_local/commands/bridge_commands.py",
    "grok_local/commands/checkpoint_commands.py",
    "grok_local/commands/misc_commands.py",
    "scripts/test_bridge_e2e.sh",
    "grok_checkpoint.py",
    "git_ops.py",
    "file_ops.py",
]

# Files changed or added in this session (Mar 05, 2025)
RECENT_FILES = [
    "grok_local/command_handler.py",
    "grok_local/__main__.py",
    "grok_local/grok_bridge.py",
    "scripts/test_bridge_e2e.sh",
    "grok_local/commands/__init__.py",
    "grok_local/commands/git_commands.py",
    "grok_local/commands/file_commands.py",
    "grok_local/commands/bridge_commands.py",
    "grok_local/commands/checkpoint_commands.py",
    "grok_local/commands/misc_commands.py",
]

def generate_prompt(most_recent=False):
    preamble = (
        "The following contains information to restart a Grok 3 chat session for Grok-Local development. "
        "We are currently enhancing grok_local, a CLI agent for managing files, Git repos, and agent communication. "
        "We’ve modularized command_handler.py into commands/ submodules and integrated grok_bridge.py for autonomous "
        "agent interaction, verified by scripts/test_bridge_e2e.sh. Next, we aim to refine CLI features and explore X polling. "
        "The text below includes project structure, instructions, and recent files to guide you.\n\n"
    )
    prompt = preamble + (
        "# Grok-Local Bootstrap Context (Mar 05, 2025)\n"
        "# Mission: Build a fully autonomous local agent for managing project files, Git repos, "
        "communicating with users and agents, and solving problems collaboratively.\n"
        "# Progress: Modular CLI with bridge integration, Git ops, and checkpointing.\n\n"
        "## Recent Work (Mar 05, 2025)\n"
        "- Modularized `command_handler.py` into `commands/` subpackage for scalability.\n"
        "- Integrated `grok_bridge.py` with CLI for autonomous agent communication.\n"
        "- Added `test_bridge_e2e.sh` for end-to-end testing of bridge and checkpoint flows.\n\n"
        "## Current Task\n"
        "- Enhanced `grok_bootstrap.py --most-recent` to include recent file contents with preamble.\n\n"
        "## Critical Files\n"
    )
    for file in CRITICAL_FILES:
        if os.path.exists(file):
            prompt += f"- `{file}`: {os.path.getsize(file)} bytes, last modified {datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            prompt += f"- `{file}`: Missing locally, fetch from Git\n"
    prompt += (
        "\n## Instructions\n"
        "- Use these files to restart dev chats with current context.\n"
        "- Fetch missing files from git@github.com:imars/grok-local.git if needed.\n"
    )
    
    if most_recent:
        prompt += "\n## Recently Changed/Added Files (Mar 05, 2025)\n"
        for file in RECENT_FILES:
            if os.path.exists(file):
                prompt += f"\n### {file}\n```python\n"
                with open(file, 'r') as f:
                    prompt += f.read()
                prompt += "\n```\n"
            else:
                prompt += f"\n### {file}\nMissing locally, fetch from Git\n"
    
    return prompt

def dump_files():
    for file in CRITICAL_FILES:
        if os.path.exists(file):
            print(f"\n# {file}\n")
            with open(file, 'r') as f:
                print(f.read())
        else:
            print(f"\n# {file}\n# Missing locally\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grok-Local Bootstrap: Restart dev chats with context.")
    parser.add_argument("--dump", action="store_true", help="Dump full contents of critical files.")
    parser.add_argument("--prompt", action="store_true", help="Generate chat-ready summary.")
    parser.add_argument("--most-recent", action="store_true", help="Include summary and contents of recently changed/added files.")
    args = parser.parse_args()

    if args.dump:
        dump_files()
    elif args.prompt:
        print(generate_prompt(most_recent=False))
    elif args.most_recent:
        print(generate_prompt(most_recent=True))
    else:
        print("Run with --dump, --prompt, or --most-recent for output.")
