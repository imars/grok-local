import os
import shutil
import git
from git import Repo

def create_file(file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write('')
        return f"Created file: {file_path}"
    except Exception as e:
        return f"Error creating file {file_path}: {str(e)}"

def delete_file(file_path):
    try:
        os.remove(file_path)
        return f"Deleted file: {file_path}"
    except Exception as e:
        return f"Error deleting file {file_path}: {str(e)}"

def move_file(src, dst):
    try:
        shutil.move(src, dst)
        return f"Moved file from {src} to {dst}"
    except Exception as e:
        return f"Error moving file from {src} to {dst}: {str(e)}"

def copy_file(src, dst):
    try:
        shutil.copy2(src, dst)
        return f"Copied file from {src} to {dst}"
    except Exception as e:
        return f"Error copying file from {src} to {dst}: {str(e)}"

def read_file(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

def write_file(file_path, content):
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Wrote to file: {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {str(e)}"

def append_file(file_path, content):
    try:
        with open(file_path, 'a') as f:
            f.write(content)
        return f"Appended to file: {file_path}"
    except Exception as e:
        return f"Error appending to file {file_path}: {str(e)}"

def list_files(directory):
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files in {directory}: {str(e)}"

def rename_file(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"Renamed file from {old_path} to {new_path}"
    except Exception as e:
        return f"Error renaming file from {old_path} to {new_path}: {str(e)}"

def clean_cruft(directory):
    """Remove temporary or cruft files like .pyc, .pyo, or macOS ._ files in the given directory."""
    try:
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.pyc', '.pyo')) or file.startswith('._'):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                    count += 1
        return f"Cleaned {count} cruft files from {directory}"
    except Exception as e:
        return f"Error cleaning cruft in {directory}: {str(e)}"
