#!/usr/bin/env python3
# grok_local/command_handler.py
import os
import logging
import requests
import uuid
import time
from .config import PROJECT_DIR, LOCAL_DIR
logger = logging.getLogger()
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file, clean_cruft
from git_ops import get_git_interface
from grok_checkpoint import save_checkpoint, list_checkpoints
from .utils import what_time_is_it, report

BRIDGE_URL = "http://0.0.0.0:5000"

def process_multi_command(request, ai_adapter, git_interface, debug=False):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd, ai_adapter, git_interface, debug)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def ask_local(request, ai_adapter, git_interface, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.debug(f"Debug processing: {request}")
    logger.info(f"Processing command: {request}")

    if "&&" in request:
        return process_multi_command(request, ai_adapter, git_interface, debug)

    req_lower = request.lower()
    if req_lower.startswith("grok "):
        prompt = request[5:].strip()
        return report(ai_adapter.delegate(prompt))
    elif req_lower.startswith("send to grok "):
        message = request[12:].strip()
        req_id = str(uuid.uuid4())
        try:
            response = requests.post(f"{BRIDGE_URL}/channel", json={"input": message, "id": req_id}, timeout=5)
            if response.status_code != 200:
                logger.error(f"Bridge POST failed: {response.text}")
                return report(f"Failed to send to Grok: {response.text}")
            # Poll for response
            max_attempts = 10
            delay = 2  # seconds
            for attempt in range(max_attempts):
                resp = requests.get(f"{BRIDGE_URL}/get-response", params={"id": req_id}, timeout=5)
                if resp.status_code == 200:
                    return report(f"Grok response: {resp.text}")
                elif resp.status_code != 404:
                    logger.error(f"Bridge GET failed: {resp.text}")
                    return report(f"Error fetching response: {resp.text}")
                logger.info(f"Waiting for Grok response (attempt {attempt + 1}/{max_attempts})")
                time.sleep(delay)
            return report("No response from Grok within timeout")
        except requests.RequestException as e:
            logger.error(f"Bridge connection failed: {e}")
            return report(f"Error: Could not connect to bridge at {BRIDGE_URL}")
    elif req_lower in ["what time is it", "ask what time is it"]:
        return report(what_time_is_it())
    elif req_lower == "version":
        return report("grok-local v0.1")
    elif req_lower == "clean repo":
        cruft_result = clean_cruft()
        git_result = git_interface.git_clean_repo()
        return report(f"{cruft_result}\n{git_result}")
    elif req_lower == "list files":
        return report(list_files())
    elif req_lower == "list checkpoints":
        return report(list_checkpoints())
    elif req_lower.startswith("checkpoint "):
        description = request[10:].strip()
        if not description:
            return "Error: Checkpoint requires a description"
        parts = description.split(" --file ")
        desc = parts[0].strip("'")
        filename = parts[1].split()[0].strip("'") if len(parts) > 1 else "checkpoint.json"
        content = None
        chat_url = None
        git_update = "--git" in description
        if git_update:
            desc = desc.replace(" --git", "").strip()

        params = " ".join(parts[1:]) if len(parts) > 1 else parts[0]
        if "with current x_poller.py content" in params:
            try:
                with open("x_poller.py", "r") as f:
                    content = f.read()
            except FileNotFoundError:
                logger.error("x_poller.py not found for checkpoint")
                return "Error: x_poller.py not found"
        for param in params.split():
            if param.startswith("chat_url="):
                chat_url = param.split("=", 1)[1].strip("'")

        return report(save_checkpoint(desc, git_interface, filename=filename, file_content=content, chat_url=chat_url, git_update=git_update))
    elif req_lower.startswith("commit "):
        full_message = request[6:].strip()
        if full_message.startswith("'") and full_message.endswith("'"):
            full_message = full_message[1:-1]
        elif full_message.startswith('"') and full_message.endswith('"'):
            full_message = full_message[1:-1]
        parts = full_message.split("|")
        message = parts[0] or "Automated commit"
        commit_message = full_message if len(parts) == 1 else message
        result = git_interface.commit_and_push(commit_message)
        if "failed" in result.lower():
            logger.error(result)
            return result
        return report(result)
    elif req_lower.startswith("git push"):
        parts = request.split()
        if len(parts) >= 4 and parts[2] == "origin":
            branch = parts[3]
            return report(git_interface.git_push(branch))
        return report("Error: Invalid git push command format. Use 'git push origin <branch>'")
    elif req_lower == "git status":
        return report(git_interface.git_status())
    elif req_lower == "git pull":
        return report(git_interface.git_pull())
    elif req_lower.startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        return report(git_interface.git_log(count))
    elif req_lower == "git branch":
        return report(git_interface.git_branch())
    elif req_lower.startswith("git checkout "):
        branch = request[12:].strip()
        return report(git_interface.git_checkout(branch))
    elif req_lower.startswith("git rm "):
        filename = request[6:].strip()
        return report(git_interface.git_rm(filename))
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        path, fname = os.path.split(filename)
        path = os.path.join(PROJECT_DIR, path) if path else None
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
        src_path = os.path.join(PROJECT_DIR, src_path) if src_path else None
        dst_path = os.path.join(PROJECT_DIR, dst_path) if dst_path else None
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
    elif req_lower.startswith("create spaceship fuel script"):
        response = ai_adapter.delegate("Generate a Python script simulating a spaceship's fuel consumption.")
        if "Error" not in response:
            filename = "spaceship_fuel.py"
            logger.info(f"Generated script:\n{response}")
            write_file(filename, response.strip(), path=LOCAL_DIR)
            git_interface.commit_and_push(f"Added {filename} from AI in local/")
            return report(f"Created {filename} with fuel simulation script in local/ directory.")
        return report(response)
    elif req_lower.startswith("create x login stub"):
        response = ai_adapter.delegate("Generate a Python script that simulates an X login process as a stub for x_poller.py...")
        if "Error" not in response:
            filename = "local/x_login_stub.py"
            logger.info(f"Generated X login stub:\n{response}")
            write_file(filename, response.strip(), path=None)
            move_file("x_login_stub.py", "x_login_stub.py", src_path=PROJECT_DIR, dst_path=LOCAL_DIR)
            git_interface.commit_and_push("Added X login stub for testing")
            return report(f"Created {filename} with X login stub and committed.")
        return report(response)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"
