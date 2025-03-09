import os
from datetime import datetime
import pyperclip
import argparse
import sys

def copy_files_to_clipboard(file_paths):
    """Copy contents of specified files to the clipboard with timestamps."""
    if not file_paths:
        return "No files provided to copy."
    
    content = []
    missing_files = []
    for path in file_paths:
        if os.path.exists(path):
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(path))
                with open(path, 'r', encoding='utf-8') as f:
                    mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                    content.append(f"--- {path} [Last modified: {mod_time_str}] ---\n{f.read()}\n")
            except Exception as e:
                content.append(f"--- {path} ---\nError reading file: {str(e)}\n")
        else:
            missing_files.append(path)
    
    if missing_files:
        print(f"Warning: Files not found or inaccessible: {', '.join(missing_files)}")
    
    if not content:
        return "No valid file contents to copy."
    
    full_content = "\n".join(content)
    try:
        pyperclip.copy(full_content)
        return f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard"
    except Exception as e:
        return f"Failed to copy to clipboard: {str(e)} (ensure 'pyperclip' is installed with 'pip install pyperclip')"

def get_most_recent_files(directory):
    """Get all files in the directory sorted by modification time, excluding __pycache__."""
    file_info = []
    for root, dirs, files in os.walk(directory):
        if "__pycache__" in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(path))
                file_info.append((path, mod_time))
            except Exception:
                continue
    
    file_info.sort(key=lambda x: x[1], reverse=True)  # Sort by mod time, newest first
    return [path for path, _ in file_info]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy grok_local files to clipboard")
    parser.add_argument("--most-recent", type=int, nargs="?", const=-1, help="Copy the N most recently modified files in grok_local (omit N for all files)")
    parser.add_argument("files", nargs="*", help="List of files to copy (if --most-recent is not used)")
    args = parser.parse_args()
    
    if args.most_recent is not None:
        if args.files:
            print("Warning: --most-recent ignores provided file list; scanning grok_local directory.")
        # Scan grok_local for all files
        all_files = get_most_recent_files("grok_local")
        # Select N most recent or all if N is not specified (const=-1 triggers all)
        selected_files = all_files[:args.most_recent] if args.most_recent > 0 else all_files
        result = copy_files_to_clipboard(selected_files)
    else:
        if not args.files:
            print("Error: No files specified. Usage: python copycb.py file1 file2 ... [--most-recent [N]]")
            sys.exit(1)
        selected_files = args.files
        result = copy_files_to_clipboard(selected_files)
    
    print(result)
