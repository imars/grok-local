import os
import sys
import subprocess
import argparse
import datetime
import git
from git import Repo
import shutil

PROJECT_DIR = os.getcwd()

def report_to_grok(response):
    return response  # Simplified for local use, no X reporting yet

def create_file(filename):
    try:
        with open(os.path.join(PROJECT_DIR, filename), "w") as f:
            f.write("")
        return f"Created file: {filename}"
    except Exception as e:
        return f"Error creating file: {e}"

def delete_file(filename):
    try:
        os.remove(os.path.join(PROJECT_DIR, filename))
        return f"Deleted file: {filename}"
    except Exception as e:
        return f"Error deleting file: {e}"

def move_file(src, dst):
    try:
        shutil.move(os.path.join(PROJECT_DIR, src), os.path.join(PROJECT_DIR, dst))
        return f"Moved {src} to {dst}"
    except Exception as e:
        return f"Error moving file: {e}"

def read_file(filename):
    try:
        with open(os.path.join(PROJECT_DIR, filename), "r") as f:
            content = f.read()
        return f"Content of {filename}: {content}"
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filename, content):
    try:
        with open(os.path.join(PROJECT_DIR, filename), "w") as f:
            f.write(content)
        return f"Wrote to {filename}: {content}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_files():
    try:
        files = os.listdir(PROJECT_DIR)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

def git_status():
    try:
        repo = Repo(PROJECT_DIR)
        return repo.git.status()
    except Exception as e:
        return f"Git status error: {e}"

def git_pull():
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.pull()
        return "Pulled latest changes"
    except Exception as e:
        return f"Git pull error: {e}"

def git_log(count=1):
    try:
        repo = Repo(PROJECT_DIR)
        return repo.git.log(f"-{count}")
    except Exception as e:
        return f"Git log error: {e}"

def git_branch():
    try:
        repo = Repo(PROJECT_DIR)
        return repo.git.branch()
    except Exception as e:
        return f"Git branch error: {e}"

def git_checkout(branch):
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.checkout(branch)
        return f"Checked out branch: {branch}"
    except Exception as e:
        return f"Git checkout error: {e}"

def git_commit_and_push(message="Automated commit"):
    repo = Repo(PROJECT_DIR)
    try:
        repo.git.add(A=True)
        status = repo.git.status()
        if "nothing to commit" in status:
            return "Nothing to commit"
        repo.git.commit(m=message)
        repo.git.push()
        return f"Committed and pushed: {message}"
    except git.GitCommandError as e:
        return f"Git error: {str(e)}"

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%I:%M %p GMT, %B %d, %Y")

def process_multi_command(request):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd)
        results.append(result)
    return "\n".join(results)

def ask_local(request, debug=False):
    request = request.strip()
    if debug:
        print(f"Processing: {request}")
    
    if "&&" in request:
        return process_multi_command(request)
    
    if request.lower() == "what time is it?" or request.lower() == "ask what time is it":
        return report_to_grok(what_time_is_it())
    elif request.lower() == "list files":
        return report_to_grok(list_files())
    elif request.lower().startswith("commit "):
        message = request[7:].strip() or "Automated commit"
        return report_to_grok(git_commit_and_push(message))
    elif request.lower() == "git status":
        return report_to_grok(git_status())
    elif request.lower() == "git pull":
        return report_to_grok(git_pull())
    elif request.lower().startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        return report_to_grok(git_log(count))
    elif request.lower() == "git branch":
        return report_to_grok(git_branch())
    elif request.lower().startswith("git checkout "):
        branch = request[12:].strip()
        return report_to_grok(git_checkout(branch))
    elif request.lower().startswith("create file "):
        filename = request[11:].strip()
        return report_to_grok(create_file(filename))
    elif request.lower().startswith("delete file "):
        filename = request[11:].strip()
        return report_to_grok(delete_file(filename))
    elif request.lower().startswith("move file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            return "Error: Invalid move command format. Use 'move file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(move_file(src.strip(), dst.strip()))
    elif request.lower().startswith("read file "):
        filename = request[9:].strip()
        return report_to_grok(read_file(filename))
    elif request.lower().startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            return "Error: Invalid write command format. Use 'write <content> to <filename>'"
        content, filename = parts
        return report_to_grok(write_file(filename.strip(), content.strip()))
    else:
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
