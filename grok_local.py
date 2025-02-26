import requests
import git
import os
import subprocess
import sys
import time
from git.exc import GitCommandError
import argparse
import shlex
import datetime
import json
import platform
from x_poller import ask_grok

PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
SAFE_COMMANDS = {"grep", "tail", "cat", "ls", "dir", "head", "git", "echo", "type", "whoami"}

def git_commit_and_push(message="Automated commit"):
    repo = git.Repo(PROJECT_DIR)
    try:
        repo.git.add(A=True)
        status = repo.git.status()
        if "nothing to commit" in status:
            return "Nothing to commit"
        repo.git.commit(m=message)
        repo.git.push()
        return f"Committed and pushed: {message}"
    except GitCommandError as e:
        return f"Git error: {str(e)}"

def read_file(filename):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        return f.read()

def write_file(filename, content):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)

def run_command(command_str):
    parts = shlex.split(command_str)
    cmd = parts[0].strip('"')
    if not parts or cmd.lower() not in SAFE_COMMANDS:
        return f"Error: Only {', '.join(SAFE_COMMANDS)} allowed"
    if any(danger in command_str.lower() for danger in ["sudo", "rm", "del", ";", "&", "|"]):
        return "Error: Unsafe command"
    args = [arg if not arg.startswith('/') else os.path.join(PROJECT_DIR, arg[1:]) for arg in parts[1:]]
    full_cmd = [cmd] + args
    try:
        result = subprocess.run(full_cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def report_to_grok(result):
    for attempt in range(3):
        response = ask_grok(f"GROK_LOCAL_RESULT: {result}", headless=True)
        if "Error" not in str(response) and "failed" not in str(response).lower():
            return result
        time.sleep(5)
    print(f"Failed to report to Grok 3 after 3 attempts: {result}")
    return result

def ask_local(request, debug=False):
    request = request.strip()
    if debug:
        print(f"Processing: {request}")
    if any(cmd in request.lower() for cmd in SAFE_COMMANDS):
        return report_to_grok(run_command(request))
    if request.lower() in ["what time is it?", "ask what time is it"]:
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%I:%M %p GMT, %B %d, %Y")
        return report_to_grok(current_time)
    if request.lower() == "list files":
        files = "\n".join(os.listdir(PROJECT_DIR))
        return report_to_grok(files)
    if request.lower() == "system info":
        info = f"OS: {platform.system()} {platform.release()}\nPython: {sys.version.split()[0]}"
        return report_to_grok(info)
    if request.lower().startswith("commit "):
        message = request[7:].strip() or "Automated commit"
        return report_to_grok(git_commit_and_push(message))
    if request.lower() == "scan chat":
        return report_to_grok("Current chat content scanned (full content returned by x_poller)")
    if request == "No GROK_LOCAL found after full scan":
        return "Chat scanned, no valid commands found"
    return report_to_grok(local_reasoning(request))

def local_reasoning(task):
    try:
        payload = {"model": MODEL, "messages": [{"role": "user", "content": task}]}
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120)
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                if "message" in chunk and "content" in chunk["message"]:
                    full_response += chunk["message"]["content"]
                if chunk.get("done", False):
                    break
        return full_response if full_response else "No response from Ollama"
    except requests.exceptions.RequestException as e:
        return f"Ollama error: {e}"

def command_prompt():
    print("Commands: optimize <file>, commit <message>, run <cmd>, ask <request>, exit")
    while True:
        raw_cmd = input("> ").strip()
        if not raw_cmd:
            continue
        parts = shlex.split(raw_cmd)
        action = parts[0].lower()
        if len(parts) < 2 and action != "exit":
            print("Error: Command requires an argument")
            continue

        if action == "exit":
            print("Goodbye!")
            break
        elif action == "optimize":
            filename = parts[1]
            if not os.path.exists(os.path.join(PROJECT_DIR, filename)):
                print(f"File {filename} not found")
                continue
            code = read_file(filename)
            prompt = f"Optimize this code:\n{code}"
            response = local_reasoning(prompt)
            print(f"Optimized:\n{response}")
            if "```python" in response:
                code = response.split('```python\n')[1].split('```')[0].strip()
                write_file(filename, code)
                print(f"Updated {filename}")
        elif action == "commit":
            message = " ".join(parts[1:]) or "Automated commit"
            print(git_commit_and_push(message))
        elif action == "run":
            cmd_str = " ".join(parts[1:])
            print(run_command(cmd_str))
        elif action == "ask":
            request = " ".join(parts[1:])
            result = ask_local(request, debug=True)
            print(f"{result}")
        else:
            print("Unknown command")

def main():
    parser = argparse.ArgumentParser(description="Grok-Local Agent")
    parser.add_argument("--ask", type=str, help="Run a single ask request and exit")
    args = parser.parse_args()

    if args.ask:
        print(ask_local(args.ask))
    else:
        command_prompt()

if __name__ == "__main__":
    main()
