#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import argparse
from logging.handlers import RotatingFileHandler

# Grok-Local Bootstrap Script (Feb 28, 2025): Restarts dev chat sessions with context.
# - Options: --dump (full file contents), --prompt (chat-ready summary), or run grok_local.py directly.
# - Update: Modify CRITICAL_FILES and goals via `git commit -m "Updated bootstrap for <reason>"` when files or structure change (e.g., slow chats, new features).
#
# Mission Statement:
# Grok-Local aims to become a fully autonomous local agent, managing project files and Git repos,
# communicating with users and multiple agents (local/remote), and solving problems collaboratively.
# Progress: Robust CLI (grok_local.py) with file/Git ops, checkpointing system (grok_checkpoint.py),
# X polling stubs (x_poller.py), and slimmed bootstrap script (~150 lines).
#
# Recent Work (Feb 28, 2025):
# - Slimmed this script from thousands to ~150 lines, removing embedded files.
# - Moved checkpoint logic to grok_checkpoint.py, added list/save functionality.
# - Integrated x_login_stub.py into x_poller.py for stubbed X polling.
#
# Goals:
# - Short-Term (Mar 2025): Enhance --help across scripts, harden git_commit_and_push with retries.
# - Mid-Term (Apr-May 2025): Improve checkpoint listing (metadata), add restore functionality.
# - Long-Term (Jun 2025+): Implement real X polling, enable multi-agent communication via Grok 3.

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CRITICAL_FILES = {
    "grok_local.py": "Core CLI logic for file/Git ops and Grok 3 delegation",
    "file_ops.py": "File operation utilities (create, delete, move, etc.)",
    "git_ops.py": "Git operation utilities (status, commit, push, etc.)",
    "x_poller.py": "Polls X for Grok 3 commands, currently stubbed",
    ".gitignore": "Ignores temp files and dirs for Git",
    "grok.txt": "Simple memento file, purpose unclear",
    "requirements.txt": "Lists project dependencies (e.g., gitpython)",
    "bootstrap.py": "Setup script (placeholder, may be missing)",
    "run_grok_test.py": "Runs mini project workflow tests",
    "README.md": "Main project documentation",
    "grok_bootstrap.py": "Restarts dev chat sessions",
    "grok_checkpoint.py": "Manages sessions and checkpoints",
    "tests/test_grok_local.py": "Unit tests for grok_local functionality",
    "docs/timeline.md": "Project timeline and goals",
    "docs/usage.md": "Detailed CLI usage guide",
    "docs/installation.md": "Installation instructions",
    "local/x_login_stub.py": "Stub for X login simulation",
    "debug_x_poller.sh": "Debug script for x_poller.py"
}

def dump_critical_files(chat_mode=False):
    """Print current contents of critical files from disk for session restart."""
    if chat_mode:
        print("Please analyze the project files in the current directory.\n")
    print("=== Critical Files (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES.keys()):
        filepath = os.path.join(PROJECT_DIR, filename) if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(PROJECT_DIR, *filename.split("/"))
        print(f"--- {filename} ---")
        try:
            with open(filepath, "r") as f:
                print(f.read())
            logger.info(f"Dumped contents of {filename}")
        except FileNotFoundError:
            print(f"# File not found: {filepath} - assumed in Git or placeholder")
            logger.warning(f"Could not find {filename} for dumping")
        except Exception as e:
            print(f"# Error reading {filename}: {e}")
            logger.error(f"Error dumping {filename}: {e}")
        print("\n")
    print("=== End of Critical File Contents ===")

def generate_prompt(include_main=False):
    """Generate an efficient prompt for restarting a chat session."""
    with open(__file__, "r") as f:
        lines = f.readlines()
        header = "".join(lines[:20])  # Condensed header up to goals
    
    file_summary = "\nCritical Files (Feb 28, 2025):\n"
    for filename, purpose in sorted(CRITICAL_FILES.items()):
        filepath = filename if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(*filename.split("/"))
        full_path = os.path.join(PROJECT_DIR, filepath)
        state = "Exists" if os.path.exists(full_path) else "Missing locally"
        insights = "Stable Feb 28, 2025"
        if filename == "grok_bootstrap.py":
            insights = "Slimmed to ~150 lines, Feb 28, 2025"
        elif filename == "grok_checkpoint.py":
            insights = "Enhanced with checkpoint funcs, Feb 28, 2025"
        elif filename == "x_poller.py":
            insights = "Stubbed, awaiting real X polling"
        elif state == "Missing locally":
            insights = "Fetch from Git if critical"
        file_summary += f"- {filename} | Location: {filepath} | Purpose: {purpose} | State: {state} | Insights: {insights}\n"

    instructions = "\nInstructions:\n- Fetch files from git@github.com:imars/grok-local.git (e.g., `git show HEAD:<filename>`) or local disk.\n- Run `python grok_bootstrap.py --dump` for full contents.\n"

    prompt = header + file_summary + instructions

    if include_main:
        prompt += "\nMain File (grok_local.py):\n```\n"
        try:
            with open(os.path.join(PROJECT_DIR, "grok_local.py"), "r") as f:
                prompt += f.read()
        except FileNotFoundError:
            prompt += "# Not found locally, fetch from Git"
        prompt += "\n```\nAgent: Extrapolate as needed."

    logger.info("Generated efficient prompt for chat restart")
    return prompt

def start_session(debug=False, command=None, dump=False, prompt=False, include_main=False):
    """Start a grok_local session, dump files, or generate a prompt."""
    if dump:
        dump_critical_files(chat_mode=False)
        return
    if prompt:
        print(generate_prompt(include_main=include_main))
        return

    cmd = [sys.executable, os.path.join(PROJECT_DIR, "grok_local.py")]
    if debug:
        cmd.append("--debug")
    if command:
        cmd.extend(["--ask", command])
        logger.info(f"Running non-interactive command: {command}")
    else:
        logger.info("Starting interactive grok_local session...")

    try:
        logger.info("Restarting grok_local dev chat session...")
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if command and result.stdout:
            print(result.stdout)
        if result.stderr:
            logger.error(f"Stderr: {result.stderr}")
        logger.info("Grok_local session completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restart grok_local session: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Session interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restart a Grok Local dev chat session")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--command", type=str, help="Run a specific command non-interactively")
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files")
    parser.add_argument("--prompt", action="store_true", help="Generate an efficient chat prompt")
    parser.add_argument("--include-main", action="store_true", help="Include grok_local.py in prompt")
    args = parser.parse_args()

    if args.include_main and not args.prompt:
        logger.warning("--include-main requires --prompt; ignoring --include-main")
        args.include_main = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, prompt=args.prompt, include_main=args.include_main)
