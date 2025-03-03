#!/usr/bin/env python3
import os
import sys
import argparse
import datetime
import logging
import requests
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from file_ops import create_file, delete_file, move_file, copy_file, read_file, write_file, list_files, rename_file, clean_cruft
from git_ops import git_status, git_pull, git_log, git_branch, git_checkout, git_rm, git_clean_repo, get_git_interface
from grok_checkpoint import list_checkpoints, save_checkpoint
from dotenv import load_dotenv
from browser_use import Agent  # For browser-based login

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()
GROK_API_KEY = os.getenv("GROK_API_KEY")  # For API mode
GROK_USERNAME = os.getenv("GROK_USERNAME")  # For browser mode
GROK_PASSWORD = os.getenv("GROK_PASSWORD")  # For browser mode

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

class GrokComBrowserInterface(GrokInterface):
    def delegate(self, request):
        """Query Grok at grok.com using browser automation."""
        if not all([GROK_USERNAME, GROK_PASSWORD]):
            logger.debug("Missing GROK_USERNAME or GROK_PASSWORD; using stub mode")
            return f"Stubbed grok.com browser response for: {request}"
        
        try:
            agent = Agent(headless=True)  # Headless for automation
            logger.info("Navigating to grok.com login")
            agent.navigate("https://grok.com/login")  # Adjust if login URL differs
            
            # Fill login form (adjust selectors based on grok.com's HTML)
            logger.debug("Filling login form")
            agent.fill_form({
                "username": GROK_USERNAME,  # Adjust field name if needed
                "password": GROK_PASSWORD   # Adjust field name if needed
            })
            agent.submit_form()
            time.sleep(2)  # Wait for login
            
            if "login" in agent.current_url():
                logger.error("Login failed: Still on login page")
                return "Error: Login failed"
            
            logger.info("Logged in, navigating to chat")
            agent.navigate("https://grok.com/chat")  # Adjust to actual chat URL
            agent.fill_form({"message": request}, selector=".chat-input")  # Adjust selector
            agent.submit_form()
            time.sleep(2)  # Wait for response
            
            response = agent.extract_text(selector=".chat-response")  # Adjust selector
            logger.info(f"Grok.com browser response to '{request}': {response}")
            return response if response else "No response received"
        except Exception as e:
            logger.error(f"Browser login error: {str(e)}")
            return f"Error with grok.com browser: {str(e)}"
        finally:
            agent.close()

def get_grok_interface(use_stub=True):
    if use_stub:
        return StubGrok()
    return GrokComBrowserInterface() if all([GROK_USERNAME, GROK_PASSWORD]) else RealGrok()

def report_to_grok(response):
    return response

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.strftime("%I:%M %p GMT, %B %d, %Y")
    logger.info(f"Time requested: {time_str}")
    return time_str

def process_multi_command(request, grok_interface, git_interface, debug=False):
    commands = request.split("&&")
    results = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
        result = ask_local(cmd, grok_interface, git_interface, debug)
        results.append(result)
    logger.info(f"Processed multi-command: {request}")
    return "\n".join(results)

def ask_local(request, grok_interface, git_interface, debug=False):
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Debug processing: {request}")
    else:
        logger.setLevel(logging.INFO)

    if "&&" in request:
        return process_multi_command(request, grok_interface, git_interface, debug)

    req_lower = request.lower()
    if req_lower.startswith("grok "):
        prompt = request[5:].strip()
        return report_to_grok(grok_interface.delegate(prompt))
    
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
        
        return report_to_grok(save_checkpoint(desc, git_interface, filename=filename, file_content=content, chat_url=chat_url, git_update=git_update))
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
            git_interface.commit_and_push(f"Added {filename} from Grok 3 in local/")
            return report_to_grok(f"Created {filename} with fuel simulation script in local/ directory.")
        return report_to_grok(response)
    elif req_lower.startswith("create x login stub"):
        response = grok_interface.delegate("Generate a Python script that simulates an X login process as a stub for x_poller.py...")
        if "Error" not in response:
            filename = "local/x_login_stub.py"
            logger.info(f"Generated X login stub:\n{response}")
            write_file(filename, response.strip(), path=None)
            move_file("x_login_stub.py", "x_login_stub.py", src_path=PROJECT_DIR, dst_path=LOCAL_DIR)
            git_interface.commit_and_push("Added X login stub for testing")
            return report_to_grok(f"Created {filename} with X login stub and committed.")
        return report_to_grok(response)
    else:
        logger.warning(f"Unknown command received: {request}")
        return f"Unknown command: {request}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok-Local: A CLI for managing local files, Git repositories, and delegating tasks to Grok.\n\n"
                    "Supports stubbed mode for testing and browser-based login to grok.com.",
        epilog="Examples:\n"
               "  python grok_local.py --stub --ask 'grok tell me a joke'          # Stubbed grok.com query\n"
               "  python grok_local.py --ask 'grok tell me a joke'                # Browser login to grok.com\n"
               "  python grok_local.py --stub --ask 'create spaceship fuel script' # Stubbed delegation and Git\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask", type=str, help="Execute a single command and exit")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--stub", action="store_true", help="Use stubbed Grok delegation and Git operations")
    args = parser.parse_args()

    grok_interface = get_grok_interface(use_stub=args.stub)
    git_interface = get_git_interface(use_stub=args.stub)

    if args.ask:
        result = ask_local(args.ask, grok_interface, git_interface, args.debug)
        print(result)
        if "failed" in result.lower():
            sys.exit(1)
    else:
        try:
            while True:
                cmd = input("Command: ")
                if cmd.lower() == "exit":
                    break
                result = ask_local(cmd, grok_interface, git_interface, args.debug)
                print(result)
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            logger.info("Interactive mode exited via KeyboardInterrupt")
