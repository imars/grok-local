import os
import subprocess
import sys
import argparse
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_DIR = os.path.join(PROJECT_DIR, "checkpoints")
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
os.chdir(PROJECT_DIR)

# Setup logging (shared with grok_local.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

# Ensure checkpoints directory exists
if not os.path.exists(CHECKPOINT_DIR):
    os.makedirs(CHECKPOINT_DIR)
    logger.info(f"Created checkpoint directory: {CHECKPOINT_DIR}")

def list_checkpoints():
    """List available checkpoint files in the checkpoints directory."""
    checkpoint_files = [f for f in os.listdir(CHECKPOINT_DIR) if f.endswith('.json') and 'checkpoint' in f.lower()]
    if not checkpoint_files:
        logger.info("No checkpoint files found in checkpoints/")
        return "No checkpoint files found in checkpoints/"
    logger.info(f"Found checkpoint files in checkpoints/: {checkpoint_files}")
    return "\n".join(checkpoint_files)

def save_checkpoint(description, filename="checkpoint.json", current_task=""):
    """Save a checkpoint with description, files, and current task, updating grok_bootstrap.py."""
    checkpoint_data = {
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": ["grok_bootstrap.py"],  # Track grok_bootstrap.py
        "current_task": current_task
    }
    try:
        # Save checkpoint JSON in checkpoints/
        checkpoint_path = os.path.join(CHECKPOINT_DIR, filename)
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=4)
        logger.info(f"Checkpoint saved: {description} to {checkpoint_path}")

        # Update grok_bootstrap.py with current task
        bootstrap_path = os.path.join(PROJECT_DIR, "grok_bootstrap.py")
        with open(bootstrap_path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("# Current Task"):
                lines[i] = f"# Current Task (Last Checkpoint, {datetime.datetime.now().strftime('%b %d, %Y')}):\n"
                lines[i + 1] = f"# - {current_task}\n"
                break
        with open(bootstrap_path, "w") as f:
            f.writelines(lines)
        logger.info(f"Updated grok_bootstrap.py with current task: {current_task}")

        return f"Checkpoint saved: {description} to {checkpoint_path}"
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
                task_parts = parts[0].split(" --task ")
                desc = task_parts[0]
                task = task_parts[1] if len(task_parts) > 1 else ""
                return save_checkpoint(desc, current_task=task)
            elif len(parts) == 2:
                task_parts = parts[0].split(" --task ")
                desc = task_parts[0]
                task = task_parts[1] if len(task_parts) > 1 else ""
                return save_checkpoint(desc, parts[1], task)
            else:
                return "Error: Invalid checkpoint format. Use 'checkpoint \"description\" [--file <filename>] [--task \"task\"]'"
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
                    "Checkpoints save/restore project state (files and safe/ contents) in checkpoints/.",
        epilog="Examples:\n"
               "  python grok_checkpoint.py                    # Start interactive Grok-Local session\n"
               "  python grok_checkpoint.py --ask 'list files' # Execute a single command\n"
               "  python grok_checkpoint.py --ask 'list checkpoints' # List checkpoint files\n"
               "  python grok_checkpoint.py --ask 'checkpoint \"Test backup\" --file test.json --task \"Add retry logic\"' # Save a checkpoint\n"
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
