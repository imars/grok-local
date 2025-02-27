import os
import sys
import argparse
import datetime
import logging
import json
from logging.handlers import RotatingFileHandler
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file
from git_ops import git_status, git_pull, git_log, git_branch, git_checkout, git_commit_and_push, git_rm

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
CHECKPOINT_FILE = os.path.join(PROJECT_DIR, "checkpoint.json")
SAFE_DIR = os.path.join(PROJECT_DIR, "safe")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

CRITICAL_FILES = [
    "grok_local.py", "file_ops.py", "git_ops.py", "grok_checkpoint.py",
    ".gitignore", "grok.txt", "tests/test_grok_local.py", "README.md"
]

def load_checkpoint():
    """Load the last checkpoint from file."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checkpoint(description):
    """Save a checkpoint with description, critical file contents, and safe/ files."""
    checkpoint = {
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": {},
        "safe_files": {}
    }
    # Critical files
    for filename in CRITICAL_FILES:
        file_path = os.path.join(PROJECT_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                checkpoint["files"][filename] = f.read()
        else:
            checkpoint["files"][filename] = "File not found"
    # Safe directory files
    if os.path.exists(SAFE_DIR):
        for filename in os.listdir(SAFE_DIR):
            file_path = os.path.join(SAFE_DIR, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r") as f:
                    checkpoint["safe_files"][filename] = f.read()
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=4)
    logger.info(f"Saved checkpoint with description: {description}")
    return f"Checkpoint saved: {description}"

def report_to_grok(response):
    return response

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.strftime("%I:%M %p GMT, %B %d, %Y")
    logger.info(f"Time requested: {time_str}")
    return time_str

def process_multi_command(request):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def ask_local(request, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.debug(f"Debug processing: {request}")
    
    if "&&" in request:
        return process_multi_command(request)
    
    req_lower = request.lower()
    if req_lower in ["what time is it", "ask what time is it"]:
        return report_to_grok(what_time_is_it())
    elif req_lower == "list files":
        return report_to_grok(list_files())
    elif req_lower.startswith("commit "):
        message = request[7:].strip() or "Automated commit"
        return report_to_grok(git_commit_and_push(message))
    elif req_lower == "git status":
        return report_to_grok(git_status())
    elif req_lower == "git pull":
        return report_to_grok(git_pull())
    elif req_lower.startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        return report_to_grok(git_log(count))
    elif req_lower == "git branch":
        return report_to_grok(git_branch())
    elif req_lower.startswith("git checkout "):
        branch = request[12:].strip()
        return report_to_grok(git_checkout(branch))
    elif req_lower.startswith("git rm "):
        filename = request[6:].strip()
        return report_to_grok(git_rm(filename))
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        return report_to_grok(create_file(filename))
    elif req_lower.startswith("delete file "):
        parts = request[11:].strip().split(" --force")
        filename = parts[0].strip().replace("safe/", "")
        force = len(parts) > 1 and "--force" in request.lower()
        return report_to_grok(delete_file(filename, force))
    elif req_lower.startswith("move file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid move command format")
            return "Error: Invalid move command format. Use 'move file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(move_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("copy file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid copy command format")
            return "Error: Invalid copy command format. Use 'copy file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(copy_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("rename file "):
        parts = request[11:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid rename command format")
            return "Error: Invalid rename command format. Use 'rename file <old> to <new>'"
        src, dst = parts
        return report_to_grok(rename_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("read file "):
        filename = request[9:].strip().replace("safe/", "")
        return report_to_grok(read_file(filename))
    elif req_lower.startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid write command format")
            return "Error: Invalid write command format. Use 'write <content> to <filename>'"
        content, filename = parts
        return report_to_grok(write_file(filename.strip().replace("safe/", ""), content.strip()))
    elif req_lower.startswith("checkpoint "):
        description = request[10:].strip()
        if not description:
            return "Error: Checkpoint requires a description"
        return save_checkpoint(description)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Grok Agent")
    parser.add_argument("--ask", type=str, help="Command to execute")
    parser.add_argument("--resume", action="store_true", help="Display last checkpoint")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    if args.resume:
        checkpoint = load_checkpoint()
        if checkpoint:
            desc = checkpoint.get("description", "No description")
            time = checkpoint.get("timestamp", "Unknown")
            files = checkpoint.get("files", {})
            safe_files = checkpoint.get("safe_files", {})
            print(f"Last Checkpoint:\n- Description: {desc}\n- Timestamp: {time}\n- Files tracked: {', '.join(files.keys())}")
            if safe_files:
                print(f"- Safe files: {', '.join(safe_files.keys())}")
        else:
            print("No checkpoint found.")
    elif args.ask:
        print(ask_local(args.ask, args.debug))
    else:
        while True:
            cmd = input("Command: ")
            if cmd.lower() == "exit":
                break
            print(ask_local(cmd, args.debug))
