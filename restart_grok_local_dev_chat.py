#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import argparse
from logging.handlers import RotatingFileHandler

# This document must not be deleted.
#
# This document represents a brief breakdown of the state of our project (grok-local)
# as of February 28, 2025, updated post-Grok 3 beta session. It provides a solid starting
# point for any agent restarting a dev chat, mitigating session corruption in long Grok 3
# beta chats by transferring project context to a new session. Outputs critical file contents
# when run (use --dump to see), avoiding attach button issues—see Git for versioning.
#
# Mission Statement:
# The project's long-term goal is to build a fully capable local agent that can
# communicate with the user and multiple agents (local or remote), maintain and serve
# project files and Git repos, and provide information or problem-solving assistance.
#
# Digest of Work So Far:
# Started as a CLI agent managing safe/ sandboxed files and Git. Post-beta, shifted to
# local/ workspace to keep root clean, added delegation to Grok 3 (e.g., spaceship_fuel.py),
# fixed input bugs, and clarified x_poller.py’s X polling role. Now outputs file contents
# for session restarts—non-interactive mode added for scripting. CRITICAL: All file
# operations (e.g., script creation) MUST output in `cat << 'EOF' > local/<file>` format
# for easy copy-pasting into terminals—non-negotiable for usability.
#
# Project Breakdown:
# - grok-local (git@github.com:imars/grok-local.git): Local agent leveraging Deepseek-R1
#   or Llama3.2, manages GitHub repo, files, and comms with Grok 3 (project lead).
# - Modularized into:
#   - grok_local.py: Core logic, interactive/non-interactive modes, delegates to Grok 3, X comms.
#   - file_ops.py: File ops (create, delete, etc.), uses local/ (was safe/), skips safe/.
#   - git_ops.py: Git ops (status, commit, etc.), stable.
#   - x_poller.py: Polls X for tags with ChromeDriver/Selenium, offline since Feb 27, 2025.
# - Supports: File commands (sandboxed in safe/), Git commands, utilities, delegation.
#
# Current Workflow:
# - Interactive: python restart_grok_local_dev_chat.py (prompts Command: via grok_local.py)
# - Non-Interactive: python restart_grok_local_dev_chat.py --command "create spaceship fuel script"
# - Dump Contents: python restart_grok_local_dev_chat.py --dump (prints critical file contents)
# - File ops in local/ (e.g., spaceship_fuel.py), safe/ for sandboxed ops, Git manages repo.
# - Outputs: File operations MUST use `cat << 'EOF' > local/<file>.py` format—mandatory for
#   copy-paste simplicity (e.g., delegated scripts like spaceship_fuel.py). 
# - Git: Regular commits and pushes are EXPECTED during development—update repo frequently!
# - x_poller.py polls X (offline), grok_local delegates to Grok 3, this file restarts chats.
#
# Critical Files State (Feb 28, 2025):
# - grok_local.py: Core, supports --ask, delegates to Grok 3, uses x_poller, writes to local/.
# - file_ops.py: File ops, defaults to local/, skips safe/, supports path overrides.
# - git_ops.py: Git utilities, unchanged, stable.
# - x_poller.py: X polling with Selenium, offline since Feb 27, 00:48 GMT (login blocks).
# - .gitignore: Excludes safe/, logs, etc., unchanged.
# - grok.txt: Memento, purpose unclear, unchanged.
# - requirements.txt: Dependencies (Selenium, etc.), unchanged recently.
# - bootstrap.py: Setup script, unchanged.
# - run_grok_test.py: Test runner, unchanged.
# - README.md: Project doc, unchanged.
# - restart_grok_local_dev_chat.py: This file, restarts chats, outputs file contents.
# - grok_checkpoint.py: Checkpointing, unchanged.
# - tests/test_grok_local.py: Unit tests, unchanged.
# - Root: These files + safe/ (keep_me.txt), bak/ (.json), local/ (spaceship_fuel.py), __pycache__, tests/.
#
# Next Steps:
# - Fix x_poller.py login flow (headless, timeout tweaks).
# - Add --force to delete_file.
# - Harden git_commit_and_push for robust, regular Git updates—commit and push often!
# - Boost multi-agent comms (X polling + Grok 3 delegation).
#
# Insights: Chat stalls forced output-based restarts—attach button’s down! Non-interactive mode
# added for scripting. x_poller.py’s Selenium needs headless fixes. Input bugs were a slog—Ctrl+D
# works, but test handoffs early. Hint: Future me, add a state dump or export if attach revives.

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

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
    "grok_local.py", "file_ops.py", "git_ops.py", "x_poller.py", ".gitignore",
    "grok.txt", "requirements.txt", "bootstrap.py", "run_grok_test.py", "README.md",
    "restart_grok_local_dev_chat.py", "grok_checkpoint.py", "tests/test_grok_local.py"
    # Explicitly excluding start_grok_local_session.py even if present in directory
}

def dump_critical_files(chat_mode=False):
    """Print contents of all critical files for session restart, with optional chat preamble."""
    if chat_mode:
        print("Please analyse the following and use it to take the lead on this project.\n")
    print("=== Critical File Contents (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES):
        filepath = os.path.join(PROJECT_DIR, filename) if filename != "tests/test_grok_local.py" else os.path.join(PROJECT_DIR, "tests", "test_grok_local.py")
        print(f"--- {filename} ---")
        try:
            with open(filepath, "r") as f:
                content = f.read()
            print(content)
            logger.info(f"Dumped contents of {filename}")
        except FileNotFoundError:
            print(f"# File not found: {filepath} - assumed in Git or placeholder")
            logger.warning(f"Could not find {filename} for dumping")
        except Exception as e:
            print(f"# Error reading {filename}: {e}")
            logger.error(f"Error dumping {filename}: {e}")
        print("\n")
    print("=== End of Critical File Contents ===")

def start_session(debug=False, command=None, dump=False, chat=False):
    """Start a grok_local session to restart dev chat or dump file contents.
    Supports non-interactive mode with --command, content dump with --dump,
    and chat-oriented output with --chat."""
    if dump:
        dump_critical_files(chat_mode=chat)
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
    parser.add_argument("--dump", action="store_true", help="Dump contents of critical files and exit")
    parser.add_argument("--chat", action="store_true", help="Add preamble for chat agent orientation")
    args = parser.parse_args()

    # Ensure --chat only applies with --dump
    if args.chat and not args.dump:
        logger.warning("--chat flag requires --dump; ignoring --chat")
        args.chat = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, chat=args.chat)
