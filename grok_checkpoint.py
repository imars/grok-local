import os
import subprocess
import sys
import argparse
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
os.chdir(PROJECT_DIR)

# Setup logging (shared with grok_local.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

def list_checkpoints():
    """List available checkpoint files in the project directory."""
    checkpoint_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.json') and 'checkpoint' in f.lower()]
    if not checkpoint_files:
        logger.info("No checkpoint files found")
        return "No checkpoint files found"
    logger.info(f"Found checkpoint files: {checkpoint_files}")
    return "\n".join(checkpoint_files)

def save_checkpoint(description, filename="checkpoint.json"):
    """Save a simple checkpoint with description to a JSON file."""
    checkpoint_data = {
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": []  # Placeholder; could expand to include tracked files
    }
    try:
        with open(os.path.join(PROJECT_DIR, filename), "w") as f:
            json.dump(checkpoint_data, f, indent=4)
        logger.info(f"Checkpoint saved: {description} to {filename}")
        return f"Checkpoint saved: {description} to {filename}"
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        return f"Error saving checkpoint: {e}"

def start_session(command=None, resume=False):
    """Start a grok-local session, either interactive, with a command, or resuming."""
    if resume:
        args = ["python", "grok_local.py", "--resume"]
    elif command:
        if command.lower().startswith("list checkpoints"):
            return list_checkpoints()
        elif command.lower().startswith("checkpoint "):
            description = command[10:].strip()
            if not description:
                return "Error: Checkpoint requires a description"
            parts = description.split(" --file ")
            if len(parts) == 1:
                return save_checkpoint(parts[0])
            elif len(parts) == 2:
                return save_checkpoint(parts[0], parts[1])
            else:
                return "Error: Invalid checkpoint format. Use 'checkpoint \"description\" [--file <filename>]'"
        else:
            args = ["python", "grok_local.py", "--ask", command]
    else:
        args = ["python", "grok_local.py"]

    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )
    output = result.stdout.strip()
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok Checkpoint: Manage Grok-Local sessions with checkpointing.\n\n"
                    "This script starts or resumes a Grok-Local session, passing commands to grok_local.py. "
                    "Use --ask for non-interactive commands (including checkpoint operations) or --resume to view the last checkpoint. "
                    "Checkpoints save/restore project state (files and safe/ contents).",
        epilog="Examples:\n"
               "  python grok_checkpoint.py                    # Start interactive Grok-Local session\n"
               "  python grok_checkpoint.py --ask 'list files' # Execute a single command\n"
               "  python grok_checkpoint.py --ask 'list checkpoints' # List checkpoint files\n"
               "  python grok_checkpoint.py --ask 'checkpoint \"Test backup\" --file test.json' # Save a checkpoint\n"
               "  python grok_checkpoint.py --resume           # View last checkpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--resume", action="store_true", help="Resume from the last checkpoint")
    parser.add_argument("--ask", type=str, help="Run a specific command and exit (e.g., 'git status', 'list checkpoints')")
    args = parser.parse_args()

    if args.resume:
        print(start_session(resume=True))
    elif args.ask:
        print(start_session(command=args.ask))
    else:
        start_session()
