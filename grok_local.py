import os
import sys
import argparse
import datetime
import logging
from logging.handlers import RotatingFileHandler
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file, clean_cruft
from git_ops import git_status, git_pull, git_log, git_branch, git_checkout, git_commit_and_push, git_rm, git_clean_repo

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)]
)
logger = logging.getLogger(__name__)

def report_to_grok(response):
    return response

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.strftime("%I:%M %p GMT, %B %d, %Y")
    logger.info(f"Time requested: {time_str}")
    return time_str

def delegate_to_grok(request):
    """Delegate complex tasks to Grok 3 and return the response."""
    logger.info(f"Delegating to Grok 3: {request}")
    print(f"Request sent to Grok 3: {request}")
    print("Awaiting response from Grok 3... (Paste the response and press Ctrl+D or Ctrl+Z then Enter when done)")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        response = "\n".join(lines).strip()
    logger.info(f"Received response from Grok 3:\n{response}")
    return response

def process_multi_command(request):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def list_checkpoints():
    """List available checkpoint files in the project directory."""
    checkpoint_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.json') and 'checkpoint' in f.lower()]
    if not checkpoint_files:
        logger.info("No checkpoint files found")
        return "No checkpoint files found"
    logger.info(f"Found checkpoint files: {checkpoint_files}")
    return "\n".join(checkpoint_files)

def ask_local(request, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.debug(f"Debug processing: {request}")

    if "&&" in request:
        return process_multi_command(request)

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
    elif req_lower.startswith("commit "):
        message = request[7:].strip() or "Automated commit"
        return report_to_grok(git_commit_and_push(message))
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
        response = delegate_to_grok("Generate a Python script simulating a spaceship's fuel consumption.")
        if "Error" not in response:
            filename = "spaceship_fuel.py"
            logger.info(f"Generated script:\n{response}")
            write_file(filename, response.strip(), path=LOCAL_DIR)
            git_commit_and_push(f"Added {filename} from Grok 3 in local/")
            return report_to_grok(f"Created {filename} with fuel simulation script in local/ directory.")
        return report_to_grok(response)
    elif req_lower.startswith("create x login stub"):
        response = delegate_to_grok("Generate a Python script that simulates an X login process as a stub for x_poller.py. The script should: - Take username, password, and verify code as env vars (X_USERNAME, X_PASSWORD, X_VERIFY). - Simulate a login attempt with a 2-second delay to mimic network lag. - Return True for success if all vars are present, False otherwise. - Log each step (attempt, success/failure) to a file 'x_login_stub.log' with timestamps. - Save the script as 'local/x_login_stub.py' and commit it with the message 'Added X login stub for testing'.")
        if "Error" not in response:
            filename = "local/x_login_stub.py"
            logger.info(f"Generated X login stub:\n{response}")
            write_file(filename, response.strip(), path=None)  # Write to project root, then move
            move_file("x_login_stub.py", "x_login_stub.py", src_path=PROJECT_DIR, dst_path=LOCAL_DIR)
            git_commit_and_push("Added X login stub for testing")
            return report_to_grok(f"Created {filename} with X login stub and committed.")
        return report_to_grok(response)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok-Local: Manage local files, Git repos, and delegate tasks to Grok 3.\n\n"
                    "This script provides a CLI for file operations (create, delete, move, etc.), "
                    "Git commands (status, commit, pull, etc.), checkpoint management (list checkpoints), "
                    "and delegation to Grok 3 for complex tasks. Supports interactive mode or single commands via --ask. "
                    "Use && to chain commands.",
        epilog="Supported Commands:\n"
               "  FILE OPS: create file <path>, delete file <filename>, move file <src> to <dst>, "
               "copy file <src> to <dst>, rename file <old> to <new>, read file <filename>, "
               "write '<content>' to <filename>, list files\n"
               "  GIT OPS: git status, git pull, git log [count], git branch, git checkout <branch>, "
               "commit '<message>', git rm <filename>, clean repo\n"
               "  CHECKPOINT: list checkpoints\n"
               "  UTILITY: what time is it, version\n"
               "  DELEGATION: create spaceship fuel script, create x login stub\n\n"
               "Examples:\n"
               "  python grok_local.py                    # Start interactive mode\n"
               "  python grok_local.py --ask 'list files' # List files in safe/\n"
               "  python grok_local.py --ask 'list checkpoints' # List checkpoint files\n"
               "  python grok_local.py --ask 'create file docs/note.txt && write \"Hello\" to docs/note.txt' # Chain commands\n"
               "  python grok_local.py --debug            # Interactive mode with debug output",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask", type=str, help="Execute a single command and exit (e.g., 'git status')")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for commands")
    args = parser.parse_args()

    if args.ask:
        print(ask_local(args.ask, args.debug))
    else:
        try:
            while True:
                cmd = input("Command: ")
                if cmd.lower() == "exit":
                    break
                result = ask_local(cmd, args.debug)
                print(result)
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            logger.info("Interactive mode exited via KeyboardInterrupt")
