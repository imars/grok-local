#!/usr/bin/env python3
# grok_bootstrap.py (Mar 05, 2025): Restarts dev chat sessions with context.
# Options: --dump (full file contents), --prompt (chat-ready summary to clipboard), --most-recent (summary + recent files).

import argparse
import sys
import os
import datetime
import subprocess
try:
    import pyperclip
except ImportError:
    print("Warning: pyperclip not installed. Install with 'pip install pyperclip' for clipboard support.", file=sys.stderr)
    pyperclip = None

# Critical files to include in prompt (curated core list)
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
    "grok_local/tools.py",
    "scripts/test_bridge_e2e.sh",
    "grok_checkpoint.py",
    "git_ops.py",
    "file_ops.py",
]

def get_recent_files():
    try:
        cmd = ["git", "log", "--since=1.day", "--name-only", "--pretty=format:"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = set(result.stdout.splitlines())
        return [f for f in files if f and os.path.exists(f)]
    except subprocess.CalledProcessError:
        print("Warning: Failed to fetch recent files from Git, using static list.", file=sys.stderr)
        return [
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
            "grok_local/tools.py",
        ]

def generate_prompt(most_recent=False):
    preamble = (
        "The following contains information to restart a Grok 3 chat session for Grok-Local development. "
        "We are enhancing grok_local, a CLI agent for managing files, Git repos, and agent communication. "
        "It uses a modular command structure and local inference with Ollama models when available. "
        "Next, we aim to refine CLI features and explore X polling or DOM discovery.\n\n"
    )
    prompt = preamble + (
        "# Grok-Local Bootstrap Context (Mar 05, 2025)\n"
        "# Mission: Build a fully autonomous local agent for managing project files, Git repos, "
        "communicating with users and agents, and solving problems collaboratively.\n\n"
        "## Agent\n"
        "Act as Grok-Local, a CLI agent built by xAI. Your role is to assist in managing project files, "
        "Git repositories, and communicating with users and other agents. Use the modular commands in "
        "`grok_local/commands/` (e.g., `git_commands.py`, `file_commands.py`) and the `execute_command` tool "
        "in `tools.py` for local operations. For local inference, use Ollama with 'deepseek-r1:8b' when running "
        "(http://localhost:11434/api/generate). Escalate to the bridge with 'grok <command>' for bigger tasks. "
        "If issues persist (e.g., import errors), clear cached `.pyc` files with `find . -name \"*.pyc\" -exec rm -f {} \\;`.\n"
        "### Installed Local Agents (Ollama Models)\n"
        "- `deepseek-r1:8b` (ID: b06f7ffc236b, 4.9 GB, Modified: 2 weeks ago) - Primary model for local inference.\n"
        "- `deepseek-r1:latest` (ID: 0a8c26691023, 4.7 GB, Modified: 3 weeks ago)\n"
        "- `llama3.2:latest` (ID: a80c4f17acd5, 2.0 GB, Modified: 6 weeks ago)\n\n"
        "## Progress\n"
        "Modular CLI with direct execution (--do) and local inference via Ollama, bridge for escalation.\n\n"
        "## Recent Work (Mar 05, 2025)\n"
        "- Added --do for direct execution with local inference fallback.\n"
        "- Integrated Ollama for true local inference with deepseek-r1:8b.\n"
        "- Enhanced conversational responses in tools.py.\n\n"
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
        "- Ensure Ollama is running (`ollama serve`) for local inference.\n"
    )
    
    if most_recent:
        recent_files = get_recent_files()
        prompt += "\n## Recently Changed/Added Files (Mar 05, 2025)\n"
        for file in recent_files:
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
    parser.add_argument("--prompt", action="store_true", help="Generate chat-ready summary and copy to clipboard.")
    parser.add_argument("--most-recent", action="store_true", help="Include summary and contents of recently changed/added files.")
    args = parser.parse_args()

    if args.dump:
        dump_files()
    elif args.prompt:
        output = generate_prompt(most_recent=False)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
    elif args.most_recent:
        print(generate_prompt(most_recent=True))
    else:
        print("Run with --dump, --prompt, or --most-recent for output.")
