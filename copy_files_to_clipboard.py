import os
from datetime import datetime
import pyperclip

def copy_files_to_clipboard(file_paths):
    """Copy contents of specified files to the clipboard with timestamps."""
    if not file_paths:
        return "No files provided to copy."
    
    content = []
    missing_files = []
    for path in file_paths:
        if os.path.exists(path):
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
                with open(path, 'r', encoding='utf-8') as f:
                    content.append(f"--- {path} [Last modified: {mod_time}] ---\n{f.read()}\n")
            except Exception as e:
                content.append(f"--- {path} ---\nError reading file: {str(e)}\n")
        else:
            missing_files.append(path)
    
    if missing_files:
        print(f"Warning: Files not found: {', '.join(missing_files)}")
    
    if not content:
        return "No valid file contents to copy."
    
    full_content = "\n".join(content)
    try:
        pyperclip.copy(full_content)
        return f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard"
    except Exception as e:
        return f"Failed to copy to clipboard: {str(e)} (ensure 'pyperclip' is installed with 'pip install pyperclip')"

if __name__ == "__main__":
    # Bridge-related files from grok_local tree
    files_to_copy = [
        "grok_local/grok_bridge.py",
        "grok_local/commands/bridge_commands.py",
        "grok_local/tests/test_bridge_e2e.sh",
        "grok_local/command_handler.py",
        "grok_local/tools/command_executor.py"
    ]
    result = copy_files_to_clipboard(files_to_copy)
    print(result)
