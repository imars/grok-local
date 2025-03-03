import os
import subprocess
import sys
import argparse
import datetime
import json
import uuid
import logging
from logging.handlers import RotatingFileHandler
from git_ops import get_git_interface

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_DIR = os.path.join(PROJECT_DIR, "checkpoints")
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
os.chdir(PROJECT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

if not os.path.exists(CHECKPOINT_DIR):
    os.makedirs(CHECKPOINT_DIR)
    logger.info(f"Created checkpoint directory: {CHECKPOINT_DIR}")

def list_checkpoints():
    checkpoint_files = [f for f in os.listdir(CHECKPOINT_DIR) if f.endswith('.json') and 'checkpoint' in f.lower()]
    if not checkpoint_files:
        logger.info("No checkpoint files found in checkpoints/")
        return "No checkpoint files found in checkpoints/"
    logger.info(f"Found checkpoint files in checkpoints/: {checkpoint_files}")
    return "\n".join(checkpoint_files)

def save_checkpoint(description, git_interface, filename="checkpoint.json", current_task="", chat_address=None, chat_group=None, chat_url=None, file_content=None, git_update=False):
    checkpoint_data = {
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": ["grok_bootstrap.py"],
        "current_task": current_task,
        "chat_address": chat_address if chat_address else str(uuid.uuid4()),
        "chat_group": chat_group if chat_group else "default"
    }
    if chat_url:
        checkpoint_data["chat_url"] = chat_url
    if file_content:
        checkpoint_data["file_content"] = file_content
    
    try:
        checkpoint_path = os.path.join(CHECKPOINT_DIR, filename)
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=4)
        logger.info(f"Checkpoint saved: {description} to {checkpoint_path}")

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

        if git_update:
            commit_message = f"Checkpoint: {description} (Chat: {checkpoint_data['chat_address']}, Group: {checkpoint_data['chat_group']})"
            git_result = git_interface.commit_and_push(commit_message)
            logger.info(f"Git update result: {git_result}")
            return f"Checkpoint saved: {description} to {checkpoint_path}\n{git_result}"
        
        return f"Checkpoint saved: {description} to {checkpoint_path}"
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        return f"Error saving checkpoint: {e}"

def start_session(git_interface, command=None, resume=False):
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
            git_update = "--git" in description
            if git_update:
                description = description.replace(" --git", "")
            filename = None
            task = ""
            chat_address = None
            chat_group = None
            chat_url = None
            
            if len(parts) == 1:
                task_parts = parts[0].split(" --task ")
                desc = task_parts[0]
                if len(task_parts) > 1:
                    task = task_parts[1]
                for param in task_parts:
                    if param.startswith("chat_address="):
                        chat_address = param.split("=", 1)[1]
                    elif param.startswith("chat_group="):
                        chat_group = param.split("=", 1)[1]
                    elif param.startswith("chat_url="):
                        chat_url = param.split("=", 1)[1]
                return save_checkpoint(desc, git_interface, current_task=task, chat_address=chat_address, chat_group=chat_group, chat_url=chat_url, git_update=git_update)
            elif len(parts) == 2:
                task_parts = parts[0].split(" --task ")
                desc = task_parts[0]
                if len(task_parts) > 1:
                    task = task_parts[1]
                for param in task_parts + parts[1].split():
                    if param.startswith("chat_address="):
                        chat_address = param.split("=", 1)[1]
                    elif param.startswith("chat_group="):
                        chat_group = param.split("=", 1)[1]
                    elif param.startswith("chat_url="):
                        chat_url = param.split("=", 1)[1]
                return save_checkpoint(desc, git_interface, filename=parts[1], current_task=task, chat_address=chat_address, chat_group=chat_group, chat_url=chat_url, git_update=git_update)
            else:
                return "Error: Invalid checkpoint format. Use 'checkpoint \"description\" [--file <filename>] [--task \"task\"] [--git] [chat_address=<id>] [chat_group=<group>] [chat_url=<url>]'"
        else:
            args = ["python", "grok_local.py", "--ask", command]
    else:
        args = ["python", "grok_local.py"]

    result = subprocess.run(args, capture_output=True, text=True)
    output = result.stdout.strip()
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok Checkpoint: Manage Grok-Local session checkpoints.\n\n"
                    "Lists or saves checkpoints with optional Git commits, supporting stubbed Git operations.",
        epilog="Examples:\n"
               "  python grok_checkpoint.py --stub --ask 'checkpoint \"Test\" --git' # Stubbed Git commit\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--resume", action="store_true", help="Resume from the last checkpoint")
    parser.add_argument("--ask", type=str, help="Run a specific command and exit")
    parser.add_argument("--stub", action="store_true", help="Use stubbed Git operations")
    args = parser.parse_args()

    git_interface = get_git_interface(use_stub=args.stub)

    if args.resume:
        print(start_session(git_interface, resume=True))
    elif args.ask:
        print(start_session(git_interface, command=args.ask))
    else:
        start_session(git_interface)
