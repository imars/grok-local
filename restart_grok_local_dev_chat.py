#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import argparse
from logging.handlers import RotatingFileHandler

# This script restarts a Grok-Local dev chat session, providing context without embedding file contents.
# Use --dump to display current critical file contents from disk, --prompt for an efficient chat prompt,
# or run grok_local.py directly. Update CRITICAL_FILES or Project Breakdown if new files or structure changes occur.
#
# Meta-Description for Updates:
# Update this script when: (1) chat sessions slow down noticeably (e.g., response lag > 5s),
# (2) new features or files are added that aren’t reflected in CRITICAL_FILES, or (3) project
# structure shifts (e.g., new dirs like local/). How to update: (a) Run with --dump to get
# current file states, (b) adjust CRITICAL_FILES to include new critical files, (c) refresh
# Project Breakdown and Critical Files State sections with latest details from README.md
# and git log, (d) test with --prompt to ensure output is agent-friendly, (e) commit changes
# with python grok_local.py --ask "commit 'Updated restart script for <reason>'".
#
# Mission Statement:
# The project's long-term goal is to build a fully capable local agent that can
# communicate with the user and multiple agents (local or remote), maintain and serve
# project files and Git repos, and provide information or problem-solving assistance.
#
# Project Breakdown (Feb 28, 2025):
# - grok-local (git@github.com:imars/grok-local.git): Local agent leveraging Deepseek-R1
#   or Llama3.2, manages GitHub repo, files, and comms with Grok 3 (project lead).
# - Key Files: grok_local.py (core), grok_checkpoint.py (sessions/checkpoints), x_poller.py (X polling).
# - Current Workflow: Interactive via grok_local.py, non-interactive with --ask, dump via this script.
# - Next Steps: Harden git_commit_and_push, enhance multi-agent comms.

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
    "restart_grok_local_dev_chat.py": "Restarts dev chat sessions",
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
    # Header verbatim from top of file
    with open(__file__, "r") as f:
        lines = f.readlines()
        header = "".join(lines[:28])  # Up to Project Breakdown
    
    # File summaries
    file_summary = "\nCritical Files (Feb 28, 2025):\n"
    for filename, purpose in sorted(CRITICAL_FILES.items()):
        filepath = filename if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(*filename.split("/"))
        full_path = os.path.join(PROJECT_DIR, filepath)
        state = "Exists" if os.path.exists(full_path) else "Missing locally"
        insights = "Stable as of Feb 28, 2025"
        if filename == "restart_grok_local_dev_chat.py":
            insights = "Slimmed Feb 28, 2025 to remove file contents"
        elif filename == "x_poller.py":
            insights = "Stubbed login, awaiting real X polling"
        elif state == "Missing locally" and filename in {"bootstrap.py", "requirements.txt"}:
            insights = "Placeholder or recently added, fetch from Git"
        file_summary += f"- {filename} | Location: {filepath} | Purpose: {purpose} | State: {state} | Insights: {insights}\n"

    # Instructions
    instructions = "\nInstructions:\n- Fetch full contents from git@github.com:imars/grok-local.git (e.g., `git show HEAD:<filename>`) or local disk if needed.\n- Use `python restart_grok_local_dev_chat.py --dump` for a complete file dump.\n"

    prompt = header + file_summary + instructions

    # Optional main file
    if include_main:
        prompt += "\nMain File (grok_local.py):\n```\n"
        try:
            with open(os.path.join(PROJECT_DIR, "grok_local.py"), "r") as f:
                prompt += f.read()
        except FileNotFoundError:
            prompt += "# File not found locally, fetch from Git"
        prompt += "\n```\nAgent: Extrapolate from this as needed."

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
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files and exit")
    parser.add_argument("--prompt", action="store_true", help="Generate an efficient prompt for chat restart")
    parser.add_argument("--include-main", action="store_true", help="Include grok_local.py in the prompt (with --prompt)")
    args = parser.parse_args()

    if args.include_main and not args.prompt:
        logger.warning("--include-main requires --prompt; ignoring --include-main")
        args.include_main = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, prompt=args.prompt, include_main=args.include_main)
