import os
import sys
import subprocess
import argparse
import datetime
import git
from git import Repo
import shutil
import logging
from logging.handlers import RotatingFileHandler
import re

PROJECT_DIR = os.getcwd()
SAFE_DIR = os.path.join(PROJECT_DIR, "safe")  # Restricted dir for file ops
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

# Critical files to protect
CRITICAL_FILES = {"grok_local.py", "x_poller.py", ".gitignore"}

def report_to_grok(response):
    return response

def sanitize_filename(filename):
    """Ensure filename is safe and within SAFE_DIR."""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename.strip())  # Remove invalid chars
    full_path = os.path.join(SAFE_DIR, filename)
    if not full_path.startswith(SAFE_DIR + os.sep):
        logger.error(f"Invalid filename attempt: {filename}")
        return None
    if os.path.basename(filename) in CRITICAL_FILES:
        logger.error(f"Protected file access denied: {filename}")
        return None
    return filename

def ensure_safe_dir():
    """Create SAFE_DIR if it doesn’t exist."""
    if not os.path.exists(SAFE_DIR):
        os.makedirs(SAFE_DIR)
        logger.info(f"Created safe directory: {SAFE_DIR}")

def create_file(filename):
    ensure_safe_dir()
    filename = sanitize_filename(filename)
    if not filename:
        return "Error: Invalid or protected filename"
    try:
        with open(os.path.join(SAFE_DIR, filename), "w") as f:
            f.write("")
        logger.info(f"Created file: {filename}")
        return f"Created file: {filename}"
    except Exception as e:
        logger.error(f"Error creating file {filename}: {e}")
        return f"Error creating file: {e}"

def delete_file(filename):
    ensure_safe_dir()
    filename = sanitize_filename(filename)
    if not filename:
        return "Error: Invalid or protected filename"
    full_path = os.path.join(SAFE_DIR, filename)
    if not os.path.exists(full_path):
        logger.warning(f"File not found for deletion: {filename}")
        return f"File not found: {filename}"
    # Confirmation for destructive actions
    if "y" != input(f"Confirm deletion of {filename}? (y/n): ").lower():
        logger.info(f"Deletion of {filename} cancelled")
        return f"Deletion cancelled: {filename}"
    try:
        os.remove(full_path)
        logger.info(f"Deleted file: {filename}")
        return f"Deleted file: {filename}"
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        return f"Error deleting file: {e}"

def move_file(src, dst):
    ensure_safe_dir()
    src = sanitize_filename(src)
    dst = sanitize_filename(dst)
    if not (src and dst):
        return "Error: Invalid or protected filename"
    src_path = os.path.join(SAFE_DIR, src)
    dst_path = os.path.join(SAFE_DIR, dst)
    if not os.path.exists(src_path):
        logger.warning(f"Source file not found: {src}")
        return f"Source file not found: {src}"
    try:
        shutil.move(src_path, dst_path)
        logger.info(f"Moved {src} to {dst}")
        return f"Moved {src} to {dst}"
    except Exception as e:
        logger.error(f"Error moving file {src} to {dst}: {e}")
        return f"Error moving file: {e}"

def read_file(filename):
    ensure_safe_dir()
    filename = sanitize_filename(filename)
    if not filename:
        return "Error: Invalid or protected filename"
    full_path = os.path.join(SAFE_DIR, filename)
    if not os.path.exists(full_path):
        logger.warning(f"File not found for reading: {filename}")
        return f"File not found: {filename}"
    try:
        with open(full_path, "r") as f:
            content = f.read()
        logger.info(f"Read file: {filename}")
        return f"Content of {filename}: {content}"
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return f"Error reading file: {e}"

def write_file(filename, content):
    ensure_safe_dir()
    filename = sanitize_filename(filename)
    if not filename:
        return "Error: Invalid or protected filename"
    full_path = os.path.join(SAFE_DIR, filename)
    try:
        with open(full_path, "w") as f:
            f.write(content)
        logger.info(f"Wrote to {filename}: {content}")
        return f"Wrote to {filename}: {content}"
    except Exception as e:
        logger.error(f"Error writing file {filename}: {e}")
        return f"Error writing file: {e}"

def list_files():
    ensure_safe_dir()
    try:
        files = os.listdir(SAFE_DIR)
        logger.info("Listed files in safe directory")
        return "\n".join(files) if files else "No files in safe directory"
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return f"Error listing files: {e}"

def git_status():
    try:
        repo = Repo(PROJECT_DIR)
        status = repo.git.status()
        logger.info("Retrieved git status")
        return status
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return f"Git status error: {e}"

def git_pull():
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.pull()
        logger.info("Pulled latest changes")
        return "Pulled latest changes"
    except Exception as e:
        logger.error(f"Git pull error: {e}")
        return f"Git pull error: {e}"

def git_log(count=1):
    try:
        repo = Repo(PROJECT_DIR)
        log = repo.git.log(f"-{count}")
        logger.info(f"Retrieved git log with count {count}")
        return log
    except Exception as e:
        logger.error(f"Git log error: {e}")
        return f"Git log error: {e}"

def git_branch():
    try:
        repo = Repo(PROJECT_DIR)
        branches = repo.git.branch()
        logger.info("Listed git branches")
        return branches
    except Exception as e:
        logger.error(f"Git branch error: {e}")
        return f"Git branch error: {e}"

def git_checkout(branch):
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.checkout(branch)
        logger.info(f"Checked out branch: {branch}")
        return f"Checked out branch: {branch}"
    except Exception as e:
        logger.error(f"Git checkout error: {e}")
        return f"Git checkout error: {e}"

def git_commit_and_push(message="Automated commit"):
    repo = Repo(PROJECT_DIR)
    try:
        repo.git.add(A=True)
        status = repo.git.status()
        if "nothing to commit" in status:
            logger.info("Nothing to commit")
            return "Nothing to commit"
        repo.git.commit(m=message)
        repo.git.push()
        logger.info(f"Committed and pushed: {message}")
        return f"Committed and pushed: {message}"
    except git.GitCommandError as e:
        logger.error(f"Git error: {e}")
        return f"Git error: {str(e)}"

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
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        return report_to_grok(create_file(filename))
    elif req_lower.startswith("delete file "):
        filename = request[11:].strip()
        return report_to_grok(delete_file(filename))
    elif req_lower.startswith("move file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid move command format")
            return "Error: Invalid move command format. Use 'move file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(move_file(src.strip(), dst.strip()))
    elif req_lower.startswith("read file "):
        filename = request[9:].strip()
        return report_to_grok(read_file(filename))
    elif req_lower.startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid write command format")
            return "Error: Invalid write command format. Use 'write <content> to <filename>'"
        content, filename = parts
        return report_to_grok(write_file(filename.strip(), content.strip()))
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Grok Agent")
    parser.add_argument("--ask", type=str, help="Command to execute")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    if args.ask:
        print(ask_local(args.ask, args.debug))
    else:
        print("Please provide a command with --ask")
