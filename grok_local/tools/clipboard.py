import os
import pyperclip
from .logging import log_conversation

def copy_files_to_clipboard(file_paths, debug=False):
    """Copy contents of specified files to the clipboard."""
    if not file_paths:
        return "No files provided to copy."
    
    content = []
    missing_files = []
    for path in file_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content.append(f"--- {path} ---\n{f.read()}\n")
            except Exception as e:
                content.append(f"--- {path} ---\nError reading file: {str(e)}\n")
        else:
            missing_files.append(path)
    
    if missing_files:
        log_conversation(f"Warning: Files not found: {', '.join(missing_files)}")
    
    if not content:
        return "No valid file contents to copy."
    
    full_content = "\n".join(content)
    try:
        pyperclip.copy(full_content)
        log_conversation(f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard")
        if debug:
            print(f"Debug: Copied content length: {len(full_content)} bytes", file=sys.stderr)
        return f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard"
    except Exception as e:
        return f"Failed to copy to clipboard: {str(e)}"
