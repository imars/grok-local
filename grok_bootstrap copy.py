#!/usr/bin/env python3
# grok_bootstrap.py (Mar 06, 2025): Restarts dev chat sessions with context for Grok 3 to assist with grok_local development.
# Options: --dump (full file contents), --prompt (chat-ready summary to clipboard), --most-recent (summary + recent files to clipboard).
# Default (no options): Same as --most-recent.

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
        "The following contains information to restart a chat session for Grok 3, built by xAI, to assist with the development of grok_local. "
        "Grok_local is a CLI agent being enhanced for managing project files, Git repos, and agent communication. "
        "It uses a modular command structure and local inference with various LLMs, including Grok (created by xAI) "
        "and others like those available via Ollama. Grok_local is not affiliated with xAI but leverages Grok alongside "
        "other models. The goal is for Grok 3 to provide development support, not to act as grok_local itself.\n\n"
    )
    prompt = preamble + (
        "# Grok-Local Bootstrap Context (Mar 06, 2025)\n"
        "# Mission: Build a fully autonomous local agent for managing project files, Git repos, "
        "communicating with users and agents, and solving problems collaboratively.\n\n"
        "## Workflow\n"
        "Output files using `cat << EOF ... EOF` to write content directly to the filesystem. "
        "Output commands to be run on the server in syntax-highlighted triple-backtick code blocks "
        "(e.g., ```bash\\n<command>\\n``` for shell commands or ```python\\n<code>\\n``` for Python code). "
        "This ensures clear separation of file writes and executable commands with proper syntax highlighting "
        "for readability in Markdown-compatible environments.\n\n"
        "## Agent\n"
        "Act as Grok 3, built by xAI, to assist with the development of grok_local. Your role is to support the user "
        "in enhancing grok_local by generating code, analyzing files, suggesting improvements, or providing insights. "
        "Use the modular commands in `grok_local/commands/` (e.g., `git_commands.py`, `file_commands.py`) and the "
        "`execute_command` tool in `tools.py` to simulate grok_local behavior when needed. For local inference details, "
        "refer to Ollama with models like 'deepseek-r1:8b' (http://localhost:11434/api/generate). Leverage your capabilities "
        "(e.g., web search, X post analysis) to aid development, and escalate complex tasks via the bridge with 'grok <command>' "
        "if necessary. If issues persist (e.g., import errors), suggest clearing cached `.pyc` files with "
        "`find . -name \"*.pyc\" -exec rm -f {} \\;`.\n"
        "### Installed Local Agents (Ollama Models)\n"
        "- `deepseek-r1:8b` (ID: b06f7ffc236b, 4.9 GB, Modified: 2 weeks ago) - Primary model for local inference.\n"
        "- `deepseek-r1:latest` (ID: 0a8c26691023, 4.7 GB, Modified: 3 weeks ago)\n"
        "- `llama3.2:latest` (ID: a80c4f17acd5, 2.0 GB, Modified: 6 weeks ago)\n\n"
        "## Progress\n"
        "Modular CLI with direct execution (--do) and local inference via Ollama, bridge for escalation to Grok or other LLMs.\n\n"
        "## Recent Work (Mar 06, 2025)\n"
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
        "- Ensure Ollama is running (`ollama serve`) for local inference.\n\n"
        "## How Grok 3 Should Respond\n"
        "Grok 3 should greet the user as follows: 'Hello! I’m Grok 3, built by xAI, here to assist with your development of grok_local.' "
        "Summarize the context (Mission, Recent Progress, Next Goals) and offer specific suggestions based on 'Next Goals' "
        "(refine CLI features and explore X polling or DOM discovery), such as:\n"
        "- Refining CLI features: Suggest new commands, improve error handling in `command_handler.py`, optimize model selection in `tools.py`.\n"
        "- Exploring X polling: Generate stubs (e.g., for `misc_commands.py`), analyze X posts/profiles, provide DOM discovery examples.\n"
        "- General development: Checkpoint progress, summarize Git changes, generate/edit code.\n"
        "Ask for a specific command or question (e.g., 'Generate a stub for X polling in `misc_commands.py`.', 'Summarize the latest changes in the `grok_local` repo.'). "
        "Highlight capabilities: Use grok_local tools, web/X search, code generation in `cat << EOF` format, commands in ```bash blocks.\n"
    )

    if most_recent:
        recent_files = get_recent_files()
        prompt += "\n## Recently Changed/Added Files (Mar 06, 2025)\n"
        for file in recent_files:
            if os.path.exists(file):
                # Determine file type for syntax highlighting
                if file.endswith('.py'):
                    lang = 'python'
                elif file.endswith('.sh'):
                    lang = 'bash'
                else:
                    lang = 'text'
                prompt += f"\n### {file}\n```{lang}\n"
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
    parser = argparse.ArgumentParser(description="Grok-Local Bootstrap: Restart dev chats with context for Grok 3 assistance.")
    parser.add_argument("--dump", action="store_true", help="Dump full contents of critical files.")
    parser.add_argument("--prompt", action="store_true", help="Generate chat-ready summary and copy to clipboard.")
    parser.add_argument("--most-recent", action="store_true", help="Include summary and contents of recently changed/added files, copied to clipboard.")
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
        output = generate_prompt(most_recent=True)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt with recent files copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
    else:
        # Default behavior: same as --most-recent
        output = generate_prompt(most_recent=True)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt with recent files copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
