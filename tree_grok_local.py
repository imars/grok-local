import os
from datetime import datetime
import pyperclip

def generate_tree(dir_path, prefix="", exclude_dirs=None):
    """Generate an optimized directory tree string with date/time for code files/scripts and data dirs."""
    if exclude_dirs is None:
        exclude_dirs = set()
    
    # Define code/script file extensions
    code_extensions = {'.py', '.sh'}
    # Define data file extensions (to include dirs, exclude files)
    data_extensions = {'.log', '.txt', '.json', '.md'}
    
    tree_str = []
    try:
        contents = sorted(os.listdir(dir_path))
    except OSError as e:
        return f"Error accessing {dir_path}: {str(e)}"
    
    # Filter files: only code/scripts
    files = [
        name for name in contents
        if name not in exclude_dirs and
        os.path.isfile(os.path.join(dir_path, name)) and
        os.path.splitext(name)[1] in code_extensions
    ]
    
    # Identify dirs, including those with data files
    dirs = []
    for name in contents:
        path = os.path.join(dir_path, name)
        if os.path.isdir(path) and name not in exclude_dirs:
            # Check if dir contains code or data files (recursively)
            sub_contents = os.listdir(path)
            has_code_or_data = any(
                os.path.splitext(sub_name)[1] in (code_extensions | data_extensions)
                for sub_name in sub_contents if os.path.isfile(os.path.join(path, sub_name))
            ) or any(
                os.path.isdir(os.path.join(path, sub_name)) and sub_name not in exclude_dirs
                for sub_name in sub_contents
            )
            if has_code_or_data:
                dirs.append(name)
    
    # Combine files and dirs, sorted
    contents = files + dirs
    pointers = ["├── " if i < len(contents) - 1 else "└── " for i in range(len(contents))]
    
    for pointer, name in zip(pointers, contents):
        path = os.path.join(dir_path, name)
        # Get last modification time
        mod_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        if os.path.isfile(path):
            tree_str.append(f"{prefix}{pointer}{name} [{mod_time}]")
        elif os.path.isdir(path):
            tree_str.append(f"{prefix}{pointer}{name}/ [{mod_time}]")
            next_prefix = prefix + ("│   " if pointer == "├── " else "    ")
            sub_tree = generate_tree(path, next_prefix, exclude_dirs)
            if sub_tree:
                tree_str.append(sub_tree)
    
    return "\n".join(tree_str) if tree_str else ""

if __name__ == "__main__":
    tree_output = generate_tree("grok_local", exclude_dirs={"__pycache__"})
    header = "Optimized tree of grok_local (code files/scripts and data dirs with timestamps):"
    full_output = f"{header}\n{tree_output}" if tree_output else "No code files, scripts, or data directories found in grok_local."
    print(full_output)
    try:
        pyperclip.copy(full_output)
        print("\nTree copied to clipboard!")
    except Exception as e:
        print(f"\nFailed to copy to clipboard: {str(e)} (ensure 'pyperclip' is installed with 'pip install pyperclip')")
