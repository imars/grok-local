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
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")
logger = logging.getLogger(__name__)

CRITICAL_FILES = {
    "grok_local.py", "x_poller.py", ".gitignore", "file_ops.py", "git_ops.py",
    "grok.txt", "requirements.txt", "bootstrap.py", "run_grok_test.py",
    "README.md", "start_grok_local_session.py", "grok_checkpoint.py",
    "tests/test_grok_local.py"
}

# Auto-move these file patterns as cruft without prompting (if untracked)
CRUFT_PATTERNS = {".log", ".pyc", ".json", ".txt", ".DS_Store"}

def sanitize_filename(filename):
    """Ensure filename is safe."""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename.strip())
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

def ensure_local_dir():
    """Create LOCAL_DIR if it doesn’t exist."""
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)
        logger.info(f"Created local directory: {LOCAL_DIR}")

def create_file(filename, path=None):
    """Create a file at the specified path, defaulting to SAFE_DIR."""
    base_dir = path if path is not None else SAFE_DIR
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Created directory: {base_dir}")
    filename = sanitize_filename(filename)
    if not filename or filename in CRITICAL_FILES:
        return "Error: Invalid or protected filename"
    try:
        full_path = os.path.join(base_dir, filename)
        with open(full_path, "w") as f:
            f.write("")
        logger.info(f"Created file: {full_path}")
        return f"Created file: {full_path}"
    except Exception as e:
        logger.error(f"Error creating file {full_path}: {e}")
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

def move_file(src, dst, src_path=None, dst_path=None):
    """Move a file from src_path (default SAFE_DIR) to dst_path (default SAFE_DIR)."""
    src_base = src_path if src_path is not None else SAFE_DIR
    dst_base = dst_path if dst_path is not None else SAFE_DIR
    src = sanitize_filename(src)
    dst = sanitize_filename(dst)
    if not (src and dst):
        return "Error: Invalid or protected filename"
    src_full = os.path.join(src_base, src)
    dst_full = os.path.join(dst_base, dst)
    if not os.path.exists(src_full):
        logger.warning(f"Source file not found: {src_full}")
        return f"Source file not found: {src_full}"
    if not os.path.exists(dst_base):
        os.makedirs(dst_base, exist_ok=True)
        logger.info(f"Created directory: {dst_base}")
    try:
        shutil.move(src_full, dst_full)
        logger.info(f"Moved {src_full} to {dst_full}")
        return f"Moved {src_full} to {dst_full}"
    except Exception as e:
        logger.error(f"Error moving file {src_full} to {dst_full}: {e}")
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

def write_file(filename, content, path=None):
    """Write content to a file, defaulting to LOCAL_DIR unless path specified."""
    filename = sanitize_filename(filename)
    if not filename:
        return "Error: Invalid or protected filename"
    base_dir = path if path is not None else LOCAL_DIR
    ensure_local_dir()  # Ensure LOCAL_DIR exists
    full_path = os.path.join(base_dir, filename)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        logger.info(f"Wrote to {full_path}: {content}")
        return f"Wrote to {full_path}: {content}"
    except Exception as e:
        logger.error(f"Error writing file {full_path}: {e}")
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
    """Move non-critical files to bak/, untracking and committing to preserve moves."""
    ensure_bak_dir()
    moved_files = []
    try:
        repo = Repo(PROJECT_DIR)
        tracked_files = set(repo.git.ls_files().splitlines())  # Get all tracked files
        logger.info(f"Tracked files: {tracked_files}")
        for root, dirs, files in os.walk(PROJECT_DIR, topdown=True):
            # Skip .git, safe, and bak directories
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in {SAFE_DIR, BAK_DIR, os.path.join(PROJECT_DIR, ".git")}]
            for item in files:
                item_path = os.path.join(root, item)
                rel_path = os.path.relpath(item_path, PROJECT_DIR)
                logger.debug(f"Processing file: {rel_path} at {item_path}")
                # Skip if path includes 'safe/' anywhere (root or bak)
                if 'safe/' in rel_path:
                    logger.info(f"Skipping safe-related file: {rel_path}")
                    continue
                # Skip if it’s a critical file (full path match)
                if rel_path in CRITICAL_FILES:
                    logger.info(f"Keeping critical file: {rel_path}")
                    continue
                # Check filesystem presence and tracking
                exists = os.path.exists(item_path)
                is_tracked = rel_path in tracked_files
                if exists and is_tracked and sys.stdin.isatty():
                    confirm = input(f"Move tracked file {rel_path} to bak/? (y/n): ").lower()
                    decision = confirm if confirm in ["y", "n"] else "n"
                    logger.info(f"Tracked file decision for {rel_path}: {decision}")
                elif exists and (any(item.endswith(pattern) for pattern in CRUFT_PATTERNS) or "__pycache__" in rel_path):
                    decision = "y"
                    logger.info(f"Auto-moving cruft: {rel_path}")
                elif exists:
                    decision = "y"  # Untracked non-critical files auto-move
                    logger.info(f"Auto-moving untracked: {rel_path}")
                else:
                    logger.debug(f"File not found on filesystem: {rel_path}")
                    continue
                if decision == "y":
                    dst_path = os.path.join(BAK_DIR, rel_path)
                    logger.debug(f"Attempting move: {item_path} -> {dst_path}")
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    if os.path.exists(dst_path):
                        os.remove(dst_path)
                        logger.info(f"Removed existing file at: {dst_path}")
                    shutil.move(item_path, dst_path)
                    if is_tracked:
                        repo.git.rm("-r", "--cached", rel_path)
                        repo.git.add(dst_path)  # Track in bak/
                        repo.git.commit(m=f"Moved {rel_path} to bak/ and untracked")
                        logger.info(f"Untracked and committed move: {rel_path}")
                    if os.path.exists(dst_path) and not os.path.exists(item_path):
                        moved_files.append(rel_path)
                        logger.info(f"Successfully moved to bak/: {rel_path} (from {item_path} to {dst_path})")
                    else:
                        logger.error(f"Move failed: {rel_path} still at {item_path} or not at {dst_path}")
                else:
                    logger.info(f"Kept file: {rel_path}")
        return f"Cleaned cruft: {', '.join(moved_files) if moved_files else 'No cruft found'}"
    except Exception as e:
        logger.error(f"Error cleaning cruft: {e}")
        return f"Error cleaning cruft: {e}"
