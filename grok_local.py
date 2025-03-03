#!/usr/bin/env python3
import os
import sys
import argparse
import datetime
import logging
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file, clean_cruft
from git_ops import git_status, git_pull, git_log, git_branch, git_checkout, git_commit_and_push, git_rm, git_clean_repo
from grok_checkpoint import list_checkpoints, save_checkpoint

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Grok Interface
class GrokInterface(ABC):
    @abstractmethod
    def delegate(self, request):
        pass

class StubGrok(GrokInterface):
    def delegate(self, request):
        logger.debug(f"Stubbed delegation for: {request}")
        if "spaceship fuel script" in request.lower():
            return "print('Stubbed spaceship fuel script')"
        elif "x login stub" in request.lower():
            return "print('Stubbed X login script')"
        return f"Stubbed response for: {request}"

class RealGrok(GrokInterface):
    def delegate(self, request):
        logger.info(f"Delegating to Grok 3: {request}")
        print(f"Request sent to Grok 3: {request}")
        print("Awaiting response from Grok 3... (Paste the response and press Ctrl+D or Ctrl+Z then Enter)")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            response = "\n".join(lines).strip()
        logger.info(f"Received response from Grok 3:\n{response}")
        return response

def get_grok_interface(use_stub=True):
    return StubGrok() if use_stub else RealGrok()

def report_to_grok(response):
    return response

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.strftime("%I:%M %p GMT, %B %d, %Y")
    logger.info(f"Time requested: {time_str}")
    return time_str

def process_multi_command(request, grok_interface, debug=False):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd, grok_interface, debug)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def ask_local(request, grok_interface, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Debug processing: {request}")
    else:
        logger.setLevel(logging.INFO)

    if "&&" in request:
        return process_multi_command(request, grok_interface, debug)

    req_lower = request.lower()
    if req_lower in ["what time is it", "ask what time is it"]:
        return report_to_grok(what_time_is_it())
    elif req_lower == "version":
        return report_to_grok("grok-local v0.1")
    elif req_lower == "clean repo":
        cruft_result = clean_cruft()
        git_result = git_clean_repo()
        return report_to_grok(f"{cruft_result}\n{git_result}")
    elif req_lower == "list files":
        return report_to_grok(list_files())
    elif req_lower == "list checkpoints":
        return report_to_grok(list_checkpoints())
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
        
        return report_to_grok(save_checkpoint(desc, filename=filename, file_content=content, chat_url=chat_url, git_update=git_update))
    elif req_lower.startswith("commit "):
        full_message = request[6:].strip()
        if full_message.startswith("'") and full_message.endswith("'"):
            full_message = full_message[1:-1]
        elif full_message.startswith('"') and full_message.endswith('"'):
            full_message = full_message[1:-1]
        parts = full_message.split("|")
        message = parts[0] or "Automated commit"
        commit_message = full_message if len(parts) == 1 else message
        result = git_commit_and_push(commit_message)
        if "failed" in result.lower():
            logger.error(result)
            return result
        return report_to_grok(result)
    elif req_lower == "git status":
        return report_to_grok(git_status())
    elif req_lower == "git pull":
        return report_to_grok(git_pull())
    elif req_lower.startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        return report_to_grok(git_log(count))
    elif req_lower == "git branch":
        return report_to_grok(git_branch())
    elif req_lower.startswith("git checkout "):
        branch = request[12:].strip()
        return report_to_grok(git_checkout(branch))
    elif req_lower.startswith("git rm "):
        filename = request[6:].strip()
        return report_to_grok(git_rm(filename))
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        path, fname = os.path.split(filename)
        path = os.path.join(PROJECT_DIR, path) if path else None
        return report_to_grok(create_file(fname, path=path))
    elif req_lower.startswith("delete file "):
        filename = request[11:].strip().replace("safe/", "")
        return report_to_grok(delete_file(filename))
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
        return report_to_grok(move_file(src_fname, dst_fname, src_path=src_path, dst_path=dst_path))
    elif req_lower.startswith("copy file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid copy command format")
            return "Error: Invalid copy command format. Use 'copy file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(copy_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("rename file "):
        parts = request[11:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid rename command format")
            return "Error: Invalid rename command format. Use 'rename file <old> to <new>'"
        src, dst = parts
        return report_to_grok(rename_file(src.strip().replace("safe/", ""), dst.strip().replace("safe/", "")))
    elif req_lower.startswith("read file "):
        filename = request[9:].strip().replace("safe/", "")
        return report_to_grok(read_file(filename))
    elif req_lower.startswith("write "):
        parts = request[5:].strip().split(" to ")
        if len(parts) != 2:
            logger.error("Invalid write command format")
            return "Error: Invalid write command format. Use 'write <content> to <filename>'"
        content, filename = parts
        return report_to_grok(write_file(filename.strip().replace("safe/", ""), content.strip()))
    elif req_lower.startswith("create spaceship fuel script"):
        response = grok_interface.delegate("Generate a Python script simulating a spaceship's fuel consumption.")
        if "Error" not in response:
            filename = "spaceship_fuel.py"
            logger.info(f"Generated script:\n{response}")
            write_file(filename, response.strip(), path=LOCAL_DIR)
            git_commit_and_push(f"Added {filename} from Grok 3 in local/")
            return report_to_grok(f"Created {filename} with fuel simulation script in local/ directory.")
        return report_to_grok(response)
    elif req_lower.startswith("create x login stub"):
        response = grok_interface.delegate("Generate a Python script that simulates an X login process as a stub for x_poller.py. The script should: - Take username, password, and verify code as env vars (X_USERNAME, X_PASSWORD, X_VERIFY). - Simulate a login attempt with a 2-second delay to mimic network lag. - Return True for success if all vars are present, False otherwise. - Log each step (attempt, success/failure) to a file 'x_login_stub.log' with timestamps. - Save the script as 'local/x_login_stub.py' and commit it with the message 'Added X login stub for testing'.")
        if "Error" not in response:
            filename = "local/x_login_stub.py"
            logger.info(f"Generated X login stub:\n{response}")
            write_file(filename, response.strip(), path=None)
            move_file("x_login_stub.py", "x_login_stub.py", src_path=PROJECT_DIR, dst_path=LOCAL_DIR)
            git_commit_and_push("Added X login stub for testing")
            return report_to_grok(f"Created {filename} with X login stub and committed.")
        return report_to_grok(response)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok-Local: A CLI for managing local files, Git repositories, and delegating tasks to Grok 3.\n\n"
                    "This script handles file operations (create, delete, move, etc.), Git commands (status, commit, pull, etc.), "
                    "checkpoint management (save/list via grok_checkpoint.py), and task delegation to Grok 3. "
                    "Run interactively or use --ask for single commands. Use && to chain multiple commands.",
        epilog="Supported Commands:\n"
               "  FILE OPS:\n"
               "    create file <path>          - Create a new file at <path>\n"
               "    delete file <filename>      - Delete <filename> from safe/\n"
               "    move file <src> to <dst>    - Move file from <src> to <dst>\n"
               "    copy file <src> to <dst>    - Copy file from <src> to <dst>\n"
               "    rename file <old> to <new>  - Rename file from <old> to <new>\n"
               "    read file <filename>        - Read contents of <filename>\n"
               "    write '<content>' to <file> - Write <content> to <file>\n"
               "    list files                  - List files in safe/\n"
               "  GIT OPS:\n"
               "    git status                  - Show Git repository status\n"
               "    git pull                    - Pull latest changes from remote\n"
               "    git log [count]             - Show last [count] commits (default 1)\n"
               "    git branch                  - List Git branches\n"
               "    git checkout <branch>       - Switch to <branch>\n"
               "    commit '<message>'          - Commit changes with <message> (use |<path> to specify file)\n"
               "    git rm <filename>           - Remove <filename> from Git tracking\n"
               "    clean repo                  - Remove untracked files from repo\n"
               "  CHECKPOINT OPS:\n"
               "    list checkpoints            - List all checkpoint files\n"
               "    checkpoint '<desc>' [options] - Save a checkpoint with <desc>\n"
               "      Options: --file <filename>  - Save to <filename> (default: checkpoint.json)\n"
               "               --git              - Commit changes to Git after saving\n"
               "               with current x_poller.py content - Include x_poller.py content\n"
               "               chat_url=<url>     - Set chat URL (e.g., https://x.com/i/grok?...)\n"
               "  UTILITY:\n"
               "    what time is it             - Show current UTC time\n"
               "    version                    - Show Grok-Local version\n"
               "  DELEGATION:\n"
               "    create spaceship fuel script - Generate and save a fuel simulation script\n"
               "    create x login stub         - Generate and save an X login stub script\n\n"
               "Examples:\n"
               "  python grok_local.py                    # Start interactive mode\n"
               "  python grok_local.py --ask 'list files' # List files in safe/\n"
               "  python grok_local.py --stub --ask 'checkpoint \"Backup\" --file backup.json chat_url=https://x.com/i/grok?conversation=123 with current x_poller.py content' # Save checkpoint (stubbed)\n"
               "  python grok_local.py --ask 'create file docs/note.txt && write \"Hello\" to docs/note.txt' # Chain commands\n"
               "  python grok_local.py --debug            # Interactive mode with debug logs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask", type=str, help="Execute a single command and exit (e.g., 'git status')")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for commands")
    parser.add_argument("--stub", action="store_true", help="Use stubbed Grok delegation instead of real interaction")
    args = parser.parse_args()

    grok_interface = get_grok_interface(use_stub=args.stub)

    if args.ask:
        result = ask_local(args.ask, grok_interface, args.debug)
        print(result)
        if "failed" in result.lower():
            sys.exit(1)
    else:
        try:
            while True:
                cmd = input("Command: ")
                if cmd.lower() == "exit":
                    break
                result = ask_local(cmd, grok_interface, args.debug)
                print(result)
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            logger.info("Interactive mode exited via KeyboardInterrupt")
