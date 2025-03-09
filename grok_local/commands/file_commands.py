# grok_local/commands/file_commands.py
import os
import logging
from ..tools.config import PROJECTS_DIR  # Corrected import path
from ..utils import report
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file

logger = logging.getLogger(__name__)

def file_command(request):
    """Handle file-related commands."""
    req_lower = request.lower()
    if req_lower.startswith("create file "):
        filename = request[11:].strip()
        path, fname = os.path.split(filename)
        path = os.path.join(PROJECTS_DIR, path) if path else None
        return report(create_file(fname, path=path))
    elif req_lower.startswith("delete file "):
        filename = request[11:].strip().replace("safe/", "")
        return report(delete_file(filename))
    elif req_lower.startswith("move file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid move command format")
            return "Error: Invalid move command format. Use 'move file <src> to <dst>'"
        src, dst = parts
        src_path, src_fname = os.path.split(src.strip())
        dst_path, dst_fname = os.path.split(dst.strip())
        src_path = os.path.join(PROJECTS_DIR, src_path) if src_path else None
        dst_path = os.path.join(PROJECTS_DIR, dst_path) if dst_path else None
        return report(move_file(src_fname, dst_fname, src_path=src_path, dst_path=dst_path))
    elif req_lower.startswith("copy file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid copy command format")
            return "Error: Invalid copy command format. Use 'copy file <src> to <dst>'"
        src, dst = parts
        return report(copy_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("rename file "):
        parts = request[11:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid rename command format")
            return "Error: Invalid rename command format. Use 'rename file <old> to <new>'"
        src, dst = parts
        return report(rename_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("read file "):
        filename = request[9:].strip().replace("safe/", "")
        return report(read_file(filename))
    elif req_lower.startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid write command format")
            return "Error: Invalid write command format. Use 'write <content> to <filename>'"
        content, filename = parts
        return report(write_file(filename.strip().replace("safe/", ""), content.strip()))
    else:
        return f"Unknown file command: {request}"
