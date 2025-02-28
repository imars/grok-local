import os
import sys
import shutil
import re
import logging
import git
from git import Repo

PROJECT_DIR = os.getcwd()
SAFE_DIR = os.path.join(PROJECT_DIR, "safe")
BAK_DIR = os.path.join(PROJECT_DIR, "bak")
logger = logging.getLogger(__name__)

CRITICAL_FILES = {
    "grok_local.py", "x_poller.py", ".gitignore", "file_ops.py", "git_ops.py",
    "grok.txt", "requirements.txt", "bootstrap.py", "run_grok_test.py",
    "README.md", "start_grok_local_session.py", "grok_checkpoint.py"
}

# Auto-move these file patterns as cruft without prompting
CRUFT_PATTERNS = {".log", ".pyc", ".json"}

def sanitize_filename(filename):
    """Ensure filename is safe and within SAFE_DIR."""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename.strip())
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

def ensure_bak_dir():
    """Create BAK_DIR if it doesn’t exist."""
    if not os.path.exists(BAK_DIR):
        os.makedirs(BAK_DIR)
        logger.info(f"Created backup directory: {BAK_DIR}")

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
    if sys.stdin.isatty():  # Interactive mode only
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

def copy_file(src, dst):
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
        shutil.copy(src_path, dst_path)
        logger.info(f"Copied {src} to {dst}")
        return f"Copied {src} to {dst}"
    except Exception as e:
        logger.error(f"Error copying file {src} to {dst}: {e}")
        return f"Error copying file: {e}"

def rename_file(src, dst):
    return move_file(src, dst)  # Alias move for clarity

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

def clean_cruft():
    """Move non-critical files to bak/, auto-moving cruft patterns and prompting for others."""
    ensure_bak_dir()
    moved_files = []
    try:
        repo = Repo(PROJECT_DIR)
        tracked_files = set(repo.git.ls_files().splitlines())  # Get all tracked files
        for root, dirs, files in os.walk(PROJECT_DIR, topdown=True):
            # Skip .git, safe, and bak directories
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in {SAFE_DIR, BAK_DIR} and d != ".git"]
            for item in files:
                item_path = os.path.join(root, item)
                rel_path = os.path.relpath(item_path, PROJECT_DIR)
                # Skip if it’s a critical file (full path match)
                if rel_path in CRITICAL_FILES:
                    logger.info(f"Keeping critical file: {rel_path}")
                    continue
                # Skip if in safe/, bak/, or .git
                if (item_path.startswith(SAFE_DIR + os.sep) or 
                    item_path.startswith(BAK_DIR + os.sep) or 
                    item_path.startswith(os.path.join(PROJECT_DIR, ".git") + os.sep)):
                    logger.info(f"Skipping protected dir file: {rel_path}")
                    continue
                # Auto-move obvious cruft
                if any(item.endswith(pattern) for pattern in CRUFT_PATTERNS):
                    decision = "y"
                    logger.info(f"Auto-moving cruft: {rel_path}")
                # Check if tracked and prompt if not auto-moved
                elif rel_path in tracked_files and sys.stdin.isatty():
                    confirm = input(f"Move tracked file {rel_path} to bak/? (y/n): ").lower()
                    decision = confirm if confirm in ["y", "n"] else "n"
                else:
                    decision = "y"  # Untracked non-critical files auto-move
                if decision == "y":
                    dst_path = os.path.join(BAK_DIR, rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    if os.path.exists(dst_path):
                        os.remove(dst_path)
                        logger.info(f"Removed existing file at: {dst_path}")
                    shutil.move(item_path, dst_path)
                    moved_files.append(rel_path)
                    logger.info(f"Moved to bak/: {rel_path} (from {item_path} to {dst_path})")
                else:
                    logger.info(f"Kept file: {rel_path}")
        return f"Cleaned cruft: {', '.join(moved_files) if moved_files else 'No cruft found'}"
    except Exception as e:
        logger.error(f"Error cleaning cruft: {e}")
        return f"Error cleaning cruft: {e}"
