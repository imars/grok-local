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

def ensure_safe_dir():
    """Create SAFE_DIR if it doesn’t exist."""
    if not os.path.exists(SAFE_DIR):
        os.makedirs(SAFE_DIR)
        logger.info(f"Created safe directory: {SAFE_DIR}")

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checkpoint(description):
    checkpoint = {
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": {},
        "safe_files": {}
    }
    for filename in CRITICAL_FILES:
        file_path = os.path.join(PROJECT_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                checkpoint["files"][filename] = f.read()
        else:
            checkpoint["files"][filename] = "File not found"
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

def restore_checkpoint(all_files=False):
    checkpoint = load_checkpoint()
    if not checkpoint:
        return "No checkpoint found to restore"
    safe_files = checkpoint.get("safe_files", {})
    critical_files = checkpoint.get("files", {}) if all_files else {}
    if not (safe_files or critical_files):
        return "No files to restore in checkpoint"
    restored = []
    ensure_safe_dir()  # Ensure safe/ exists before restoring
    for filename, content in safe_files.items():
        file_path = os.path.join(SAFE_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)  # Overwrite existing files
        with open(file_path, "w") as f:
            f.write(content)
        logger.debug(f"Restored safe file: {filename}")
        restored.append(filename)
    if all_files:
        for filename, content in critical_files.items():
            if content != "File not found":
                file_path = os.path.join(PROJECT_DIR, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)  # Ensure overwrite
                with open(file_path, "w") as f:
                    f.write(content)
                logger.debug(f"Restored critical file: {filename}")
                restored.append(filename)
    logger.info(f"Restored files from checkpoint: {restored}")
    return f"Restored files from checkpoint: {', '.join(restored)}"

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
    if "&&" in request:
        result = process_multi_command(request)
        if any(r.startswith("Error") or r.startswith("Git") for r in result.split("\n")):
            save_checkpoint(f"Multi-command failed: {request}")
        return result
    
    req_lower = request.lower()
    if req_lower in ["what time is it", "ask what time is it"]:
        result = report_to_grok(what_time_is_it())
        return result
    elif req_lower == "list files":
        result = report_to_grok(list_files())
        return result
    elif req_lower.startswith("commit "):
        message = request[7:].strip() or "Automated commit"
        result = report_to_grok(git_commit_and_push(message))
        if result.startswith("Git error"):
            save_checkpoint(f"Commit failed: {result}")
        return result
    elif req_lower == "git status":
        result = report_to_grok(git_status())
        return result
    elif req_lower == "git pull":
        result = report_to_grok(git_pull())
        if "error" in result.lower():
            save_checkpoint(f"Git pull failed: {result}")
        return result
    elif req_lower.startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        result = report_to_grok(git_log(count))
        if result.startswith("Git error"):
            save_checkpoint(f"Git log failed: {result}")
        return result
    elif req_lower == "git branch":
        result = report_to_grok(git_branch())
        if result.startswith("Git error"):
            save_checkpoint(f"Git branch failed: {result}")
        return result
    elif req_lower.startswith("git checkout "):
        branch = request[12:].strip()
        result = report_to_grok(git_checkout(branch))
        if result.startswith("Git error"):
            save_checkpoint(f"Git checkout failed: {result}")
        return result
    elif req_lower.startswith("git rm "):
        filename = request[6:].strip()
        result = report_to_grok(git_rm(filename))
        if result.startswith("Git error"):
            save_checkpoint(f"Git rm failed: {result}")
        return result
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        result = report_to_grok(create_file(filename))
        if result.startswith("Error"):
            save_checkpoint(f"Create file failed: {result}")
        return result
    elif req_lower.startswith("delete file "):
        parts = request[11:].strip().split(" --force")
        filename = parts[0].strip().replace("safe/", "")
        force = len(parts) > 1 and "--force" in request.lower()
        result = report_to_grok(delete_file(filename, force))
        if result.startswith("Error"):
            save_checkpoint(f"Delete file failed: {result}")
        return result
    elif req_lower.startswith("move file"):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid move command format")
            result = "Error: Invalid move command format. Use 'move file <src> to <dst>'"
            save_checkpoint(f"Move file failed: {result}")
            return result
        src, dst = parts
        result = report_to_grok(move_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
        if result.startswith("Error"):
            save_checkpoint(f"Move file failed: {result}")
        return result
    elif req_lower.startswith("copy file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid copy command format")
            result = "Error: Invalid copy command format. Use 'move file <src> to <dst>'"
            save_checkpoint(f"Copy file failed: {result}")
            return result
        src, dst = parts
        result = report_to_grok(copy_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
        if result.startswith("Error"):
            save_checkpoint(f"Copy file failed: {result}")
        return result
    elif req_lower.startswith("rename file "):
        parts = request[11:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid rename command format")
            result = "Error: Invalid rename command format. Use 'rename file <old> to <new>'"
            save_checkpoint(f"Rename file failed: {result}")
            return result
        src, dst = parts
        result = report_to_grok(rename_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
        if result.startswith("Error"):
            save_checkpoint(f"Rename file failed: {result}")
        return result
    elif req_lower.startswith("read file "):
        filename = request[9:].strip().replace("safe/", "")
        result = report_to_grok(read_file(filename))
        if result.startswith("Error"):
            save_checkpoint(f"Read file failed: {result}")
        return result
    elif req_lower.startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid write command format")
            result = "Error: Invalid write command format. Use 'write <content> to <filename>'"
            save_checkpoint(f"Write file failed: {result}")
            return result
        content, filename = parts
        result = report_to_grok(write_file(filename.strip().replace("safe/", ""), content.strip()))
        if result.startswith("Error"):
            save_checkpoint(f"Write file failed: {result}")
        return result
    elif req_lower.startswith("checkpoint "):
        description = request[10:].strip()
        if not description:
            return "Error: Checkpoint requires a description"
        return save_checkpoint(description)
    elif req_lower.startswith("restore"):
        all_files = "--all" in request.lower()
        return restore_checkpoint(all_files)
    else:
        logger.warning(f"Unknown command received: {request}")
        result = f"Unknown command: {request}"
        save_checkpoint(f"Unknown command: {request}")
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Grok Agent")
    parser.add_argument("--ask", type=str, help="Command to execute")
    parser.add_argument("--resume", action="store_true", help="Display last checkpoint")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--all", action="store_true", help="Restore all files from checkpoint (including critical)")
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
