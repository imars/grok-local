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

# Config
PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
SAFE_COMMANDS = {"grep", "tail", "cat", "ls", "dir", "head"}

def git_push(message="Automated commit"):
    repo = git.Repo(PROJECT_DIR)
    repo.git.add(A=True)
    try:
        repo.git.commit(m=message)
    except GitCommandError as e:
        if "nothing to commit" in str(e):
            pass
        else:
            raise
    repo.git.push()
    return "Pushed to GitHub or already up-to-date"

def read_file(filename):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        return f.read()

def write_file(filename, content):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)

def run_command(command_str):
    print(f"Running command: {command_str}")
    parts = command_str.split()
    cmd = parts[0].strip('"')  # Strip quotes from command
    if not parts or cmd.lower() not in SAFE_COMMANDS:
        return f"Error: Only {', '.join(SAFE_COMMANDS)} allowed"
    if any(danger in command_str.lower() for danger in ["sudo", "rm", "del", ";", "&", "|"]):
        return "Error: Unsafe command"
    args = [arg if not arg.startswith('/') else os.path.join(PROJECT_DIR, arg[1:]) for arg in parts[1:]]
    full_cmd = [cmd] + args
    print(f"Executing: {full_cmd}")
    try:
        result = subprocess.run(full_cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=10)
        output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        print(f"Command output: {output}")
        return output
    except Exception as e:
        return f"Error: {e}"

def ask_local(request, debug=False):
    if debug:
        print(f"Processing ask_local: {request}")
    if any(cmd in request.lower() for cmd in SAFE_COMMANDS):
        return run_command(request)
    if "what time is it?" in request.lower():
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%I:%M %p GMT, %B %d, %Y")
        if debug:
            print(f"Returning time: {current_time}")
        return current_time
    return local_reasoning(request)

def local_reasoning(task):
    print(f"Running local_reasoning: {task}")
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
        print(f"Reasoning result: {full_response}")
        return full_response
    except requests.exceptions.RequestException as e:
        return f"Ollama error: {e}"

def command_prompt():
    print("Commands: optimize <file>, push <message>, run <cmd>, ask <request>, exit")
    while True:
        raw_cmd = input("> ").strip()
        print(f"Raw input: '{raw_cmd}'")
        if not raw_cmd:
            continue
        parts = shlex.split(raw_cmd)
        action = parts[0].lower()
        print(f"Parsed action: {action}, parts: {parts}")
        if len(parts) < 2:
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
            print(f"Optimized locally:\n{response}")
            if "```python" in response:
                code = response.split('```python\n')[1].split('```')[0].strip()
                write_file(filename, code)
                print(f"Updated {filename}")
        elif action == "push":
            print(git_push(parts[1]))
        elif action == "run":
            cmd_str = " ".join(parts[1:])
            print(run_command(cmd_str))
        elif action == "ask":
            request = " ".join(parts[1:])
            result = ask_local(request, debug=True)
            print(f"Local response:\n{result}")
        else:
            print("Unknown command. Try: optimize <file>, push <message>, run <cmd>, ask <request>, exit")

def main():
    parser = argparse.ArgumentParser(description="Grok-Local Agent")
    parser.add_argument("--ask", type=str, help="Run a single ask request and exit")
    args = parser.parse_args()

    if args.ask:
        print(ask_local(args.ask))  # No debug prints in --ask mode
    else:
        command_prompt()

if __name__ == "__main__":
    main()
