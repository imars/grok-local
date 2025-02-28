#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import argparse
from logging.handlers import RotatingFileHandler

# This script restarts a Grok-Local dev chat session, providing context without embedding file contents.
# Use --dump to display current critical file contents from disk, or run grok_local.py directly.
# Update CRITICAL_FILES or Project Breakdown if new files or structure changes occur.

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
    "grok_local.py", "file_ops.py", "git_ops.py", "x_poller.py", ".gitignore",
    "grok.txt", "requirements.txt", "bootstrap.py", "run_grok_test.py", "README.md",
    "restart_grok_local_dev_chat.py", "grok_checkpoint.py", "tests/test_grok_local.py",
    "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py",
    "debug_x_poller.sh"
}

# Project Breakdown (Feb 28, 2025):
# - grok-local: CLI agent for file/Git ops, delegates to Grok 3.
# - Key Files: grok_local.py (core), grok_checkpoint.py (sessions), x_poller.py (X polling).
# - Mission: Build a local agent for file/repo management and multi-agent comms.
# - Next Steps: Harden git_commit_and_push, enhance multi-agent comms.

def dump_critical_files(chat_mode=False):
    """Print current contents of critical files from disk for session restart."""
    if chat_mode:
        print("Please analyze the project files in the current directory.\n")
    print("=== Critical Files (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES):
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
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files and exit")
    parser.add_argument("--chat", action="store_true", help="Add preamble for chat agent orientation")
    args = parser.parse_args()

    if args.chat and not args.dump:
        logger.warning("--chat flag requires --dump; ignoring --chat")
        args.chat = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, chat=args.chat)
