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
# as of February 28, 2025, updated post-Grok 3 collaboration on X login stub, efficiency focus,
# and resolving x_poller.py logging/hang issues. It provides a solid starting point for any
# agent restarting a dev chat, mitigating session corruption in long Grok 3 beta chats by
# transferring project context to a new session. Outputs critical file contents when run
# (use --dump to see), avoiding attach button issues—see Git for versioning.
#
# Meta-Description for Updates:
# Update this script when: (1) chat sessions slow down noticeably (e.g., response lag > 5s),
# (2) new features or files are added that aren’t reflected in CRITICAL_FILES, or (3) project
# structure shifts (e.g., new dirs like local/). How to update: (a) Run with --dump to get
# current file states, (b) adjust CRITICAL_FILES to include new critical files, (c) refresh
# Project Breakdown and Critical Files State sections with latest details from README.md
# and git log, (d) test with --chat to ensure output is agent-friendly, (e) commit changes
# with git commit -m "Updated restart script for <reason>". Example trigger: Feb 28, 2025,
# updated for X login stub, docs/, path handling fixes, efficiency focus on batching steps
# via scripts (e.g., debug_x_poller.sh), parameterizing with defaults (e.g., poll_interval),
# and fixing x_poller.py logging/hang issues—key lessons from chat optimization.
#
# Mission Statement:
# The project's long-term goal is to build a fully capable local agent that can
# communicate with the user and multiple agents (local or remote), maintain and serve
# project files and Git repos, and provide information or problem-solving assistance.
#
# Digest of Work So Far:
# Started as a CLI agent managing safe/ sandboxed files and Git. Post-beta, shifted to
# local/ workspace, added delegation to Grok 3 (e.g., spaceship_fuel.py, x_login_stub.py),
# fixed input bugs, clarified x_poller.py’s X polling role with parameterized polling
# (--poll-interval, default 5s), and enhanced file ops to work outside safe/ (e.g., docs/).
# Added debug scripts (e.g., debug_x_poller.sh) for efficient testing and minimal rewrites.
# Recent focus: fixed x_poller.py silent default (no debug logs without --debug), resolved
# logging-to-file issues (switched to FileHandler, added flush), and tackled hangs with
# diagnostics and timeouts. Now outputs file contents for session restarts—non-interactive
# mode added for scripting. CRITICAL: All file operations MUST output in `cat << 'EOF' > local/<file>`
# format for easy copy-pasting into terminals—non-negotiable for usability.
#
# Project Breakdown:
# - grok-local (git@github.com:imars/grok-local.git): Local agent leveraging Deepseek-R1
#   or Llama3.2, manages GitHub repo, files, and comms with Grok 3 (project lead).
# - Modularized into:
#   - grok_local.py: Core logic, interactive/non-interactive modes, delegates to Grok 3, X comms,
#     handles arbitrary file paths.
#   - file_ops.py: File ops (create, delete, etc.), supports paths beyond safe/, skips safe/ in cruft.
#   - git_ops.py: Git ops (status, commit, etc.), stable.
#   - x_poller.py: Polls X with stubbed workflow, parameterized polling (--poll-interval, default 5s),
#     debug mode clears last_processed.txt, fixed silent default and logging issues (Feb 28, 2025).
#   - debug_x_poller.sh: Script for efficient multi-step testing of x_poller.py.
# - Supports: File commands (anywhere), Git commands, utilities, delegation with Grok 3.
#
# Current Workflow:
# - Interactive: python restart_grok_local_dev_chat.py (prompts Command: via grok_local.py)
# - Non-Interactive: python restart_grok_local_dev_chat.py --command "create file docs/new_file.txt"
# - Dump Contents: python restart_grok_local_dev_chat.py --dump (prints critical file contents)
# - File ops in local/ (e.g., x_login_stub.py), safe/ for sandbox, docs/ for docs, Git manages repo.
# - Outputs: File operations MUST use `cat << 'EOF' > local/<file>.py` format—mandatory for
#   copy-paste simplicity (e.g., delegated scripts like x_poller.py).
# - Git: Regular commits and pushes are EXPECTED—update repo frequently!
# - x_poller.py polls X (stubbed), grok_local delegates to Grok 3, this file restarts chats.
#
# Critical Files State (Feb 28, 2025):
# - grok_local.py: Core, supports --ask, delegates to Grok 3, uses x_poller, writes anywhere.
# - file_ops.py: File ops, defaults to local/, supports any path, skips safe/ in cruft.
# - git_ops.py: Git utilities, unchanged, stable.
# - x_poller.py: X polling with stubbed login/scan, --poll-interval (default 5s), --debug clears
#   last_processed.txt, fixed silent default (no debug logs without --debug), logging writes to
#   x_poller.log with FileHandler and flush (Feb 28, 2025).
# - .gitignore: Excludes safe/, logs, etc., unchanged.
# - grok.txt: Memento, purpose unclear, unchanged.
# - requirements.txt: Dependencies (gitpython), unchanged recently.
# - bootstrap.py: Setup script, unchanged.
# - run_grok_test.py: Test runner, unchanged.
# - README.md: Project doc, professionalized Feb 28, 2025.
# - restart_grok_local_dev_chat.py: This file, restarts chats, outputs file contents, updated Feb 28, 2025.
# - grok_checkpoint.py: Checkpointing, unchanged.
# - tests/test_grok_local.py: Unit tests, unchanged.
# - docs/timeline.md: Timeline and goals, added Feb 28, 2025.
# - docs/usage.md: Usage guide, added Feb 28, 2025.
# - docs/installation.md: Install guide, added Feb 28, 2025.
# - local/x_login_stub.py: X login simulation stub, added Feb 28, 2025.
# - debug_x_poller.sh: Debug script for x_poller.py, added Feb 28, 2025.
# - Root: These files + safe/ (e.g., test2.txt), bak/ (.json), local/ (x_login_stub.py, spaceship_fuel.py), docs/, __pycache__, tests/.
#
# Next Steps:
# - Implement tricky login scenario for grok_local to solve autonomously (mock server rejects 3 attempts,
#   then accepts incremented password).
# - Harden git_commit_and_push for robust Git updates—commit and push often!
# - Boost multi-agent comms (X polling + Grok 3 delegation with real X integration).
#
# Insights: Chat stalls forced output-based restarts—attach button’s down! Non-interactive mode aids
# scripting. Efficiency improved via batching steps in scripts (e.g., debug_x_poller.sh) and
# parameterizing with defaults (e.g., poll_interval) to reduce rewrites. x_poller.py logging/hang fixes
# required persistent diagnostics (prints, timeouts) and handler tweaks (FileHandler, flush)—key lessons
# from chat optimization. Test handoffs early to catch hangs.

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
    "restart_grok_local_dev_chat.py", "grok_checkpoint.py", "tests/test_grok_local.py",
    "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py",
    "debug_x_poller.sh"
}

def dump_critical_files(chat_mode=False):
    """Print contents of all critical files for session restart, with optional chat preamble."""
    if chat_mode:
        print("Please analyse the following and use it to take the lead on this project.\n")
    print("=== Critical File Contents (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES):
        filepath = os.path.join(PROJECT_DIR, filename) if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(PROJECT_DIR, *filename.split("/"))
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
    """Start a grok_local session to restart dev chat or dump file contents."""
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

    if args.chat and not args.dump:
        logger.warning("--chat flag requires --dump; ignoring --chat")
        args.chat = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, chat=args.chat)
