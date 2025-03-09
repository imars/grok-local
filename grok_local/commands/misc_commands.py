import os
from datetime import datetime
import pyperclip
from ..tools.logging import log_conversation

def generate_tree(dir_path, prefix="", exclude_dirs=None, show_timestamps=False):
    """Generate an optimized directory tree string for code files/scripts and data dirs."""
    if exclude_dirs is None:
        exclude_dirs = set()
    
    code_extensions = {'.py', '.sh'}
    data_extensions = {'.log', '.txt', '.json', '.md'}
    
    tree_str = []
    try:
        contents = sorted(os.listdir(dir_path))
    except OSError as e:
        return f"Error accessing {dir_path}: {str(e)}"
    
    files = [name for name in contents if name not in exclude_dirs and os.path.isfile(os.path.join(dir_path, name)) and os.path.splitext(name)[1] in code_extensions]
    dirs = []
    for name in contents:
        path = os.path.join(dir_path, name)
        if os.path.isdir(path) and name not in exclude_dirs:
            sub_contents = os.listdir(path)
            has_code_or_data = any(os.path.splitext(sub_name)[1] in (code_extensions | data_extensions) for sub_name in sub_contents if os.path.isfile(os.path.join(path, sub_name))) or any(os.path.isdir(os.path.join(path, sub_name)) and sub_name not in exclude_dirs for sub_name in sub_contents)
            if has_code_or_data:
                dirs.append(name)
    
    contents = files + dirs
    pointers = ["├── " if i < len(contents) - 1 else "└── " for i in range(len(contents))]
    
    for pointer, name in zip(pointers, contents):
        path = os.path.join(dir_path, name)
        if show_timestamps:
            mod_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            suffix = f" [{mod_time}]"
        else:
            suffix = ""
        if os.path.isfile(path):
            tree_str.append(f"{prefix}{pointer}{name}{suffix}")
        elif os.path.isdir(path):
            tree_str.append(f"{prefix}{pointer}{name}/{suffix}")
            next_prefix = prefix + ("│   " if pointer == "├── " else "    ")
            sub_tree = generate_tree(path, next_prefix, exclude_dirs, show_timestamps)
            if sub_tree:
                tree_str.append(sub_tree)
    
    return "\n".join(tree_str) if tree_str else ""

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
        log_conversation(f"Warning: Files not found: {', '.join(missing_files)}")
    
    if not content:
        return "No valid file contents to copy."
    
    full_content = "\n".join(content)
    try:
        pyperclip.copy(full_content)
        log_conversation(f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard")
        return f"Copied {len(file_paths) - len(missing_files)} file(s) to clipboard"
    except Exception as e:
        return f"Failed to copy to clipboard: {str(e)}"

def misc_command(command, ai_adapter, git_interface):
    command = command.strip().lower()  # Already lowercased, but ensure consistency
    if command == "what time is it":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif command == "version":
        return "grok_local v0.1.0"
    elif command == "clean repo":
        return git_interface.clean_repo()
    elif command == "list files":
        files = os.listdir(".")
        return "\n".join(files)
    elif command.startswith("copy "):
        file_paths = command.split()[1:]
        if not file_paths:
            return "No files specified to copy. Usage: copy <file1> <file2> ..."
        return copy_files_to_clipboard(file_paths)
    elif command == "tree":
        tree_output = generate_tree("grok_local", exclude_dirs={"__pycache__"})
        log_conversation("Generated directory tree for grok_local")
        return f"Directory tree of grok_local:\n{tree_output}"
    elif command == "create spaceship fuel script":
        return "TODO: Implement spaceship fuel script generation"
    elif command == "create x login stub":
        return "TODO: Implement X login stub generation"
    else:
        return f"Unknown misc command: {command}"
