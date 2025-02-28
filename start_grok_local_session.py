#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from file_ops import ensure_local_dir

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

# Setup logging - mirrors grok_local.py for consistency
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3),
        logging.StreamHandler()  # Echo to console for user feedback
    ]
)
logger = logging.getLogger(__name__)

def start_session(debug=False, command=None):
    """Start a grok_local session, ensuring local/ exists.
    
    Synopsis: This evolved from a simple launcher to support our local/ workspace,
    introduced in Feb 2025 to keep root clean. We moved from root to safe/ to local/
    for agent files like spaceship_fuel.py, reflecting grok_local's growing autonomy.
    
    Insights: Subprocess keeps it lightweight—don’t bloat this with logic; let grok_local
    handle delegation. Surprised by how input bugs in grok_local bled here—keep them separate!
    Hint: If adding features, consider a config file for paths, not hardcodes.
    
    Args:
        debug (bool): Run grok_local in debug mode.
        command (str): Optional command to pass to grok_local via --ask.
    """
    ensure_local_dir()  # Ensure grok_local’s workspace exists
    cmd = [sys.executable, os.path.join(PROJECT_DIR, "grok_local.py")]
    if debug:
        cmd.append("--debug")
    if command:
        cmd.extend(["--ask", command])
    
    try:
        logger.info("Starting grok_local session...")
        subprocess.run(cmd, check=True)
        logger.info("Grok_local session completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start grok_local session: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Session interrupted by user")
        sys.exit(0)

# Critical Files State (as of Feb 28, 2025, per our work):
# - grok_local.py: Core agent, handles commands and delegation to Grok 3, writes to local/.
# - file_ops.py: File ops (create, delete, etc.), defaults to local/ for writes, skips safe/.
# - git_ops.py: Git commands (status, commit, etc.), unchanged recently, stable.
# - x_poller.py: Unknown role (not modified), assumed critical utility.
# - .gitignore: Standard Git ignore, unchanged.
# - grok.txt: Unknown purpose (doc?), unchanged.
# - requirements.txt: Dependencies, unchanged.
# - bootstrap.py: Unknown setup script, unchanged.
# - run_grok_test.py: Test runner, unchanged.
# - README.md: Project doc, unchanged.
# - start_grok_local_session.py: This file, launches grok_local, ensures local/.
# - grok_checkpoint.py: Unknown checkpointing, unchanged.
# - tests/test_grok_local.py: Unit tests, unchanged.
# All assumed committed in Git—root is clean except these + safe/, bak/, local/, __pycache__.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a Grok Local session")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--command", type=str, help="Run a specific command non-interactively")
    args = parser.parse_args()
    
    start_session(debug=args.debug, command=args.command)
