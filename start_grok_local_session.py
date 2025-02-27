# Starting prompt for a new Grok 3 session to lead the grok-local project
print("""
We're working on a GitHub project called grok-local (git@github.com:imars/grok-local.git), a local agent that leverages Deepseek-R1 or Llama3.2 to manage a GitHub repo using local git calls, handle local file operations, and act as an agent for the user and remote agents like Grok 3. Grok 3 is the project lead, guiding development and enhancements.

Currently, grok-local drives GitHub operations (commit, status, pull, etc.) and logs into Grok 3 via ChromeDriver to operate X, bypassing manual login by saving cookies (headless or otherwise). We've streamlined the repo to include only essential files: grok_local.py (core agent logic), x_poller.py (X polling, currently offline due to login blocks), .gitignore (excludes misc/, logs, cookies), and grok.txt (a memento file). The workflow is CLI-driven, with outputs like:

cat << 'EOF' > <file_name>.py
import requests
import git...

Our repo is refreshed—extraneous files are moved to misc/, and we're focusing on enhancing grok_local.py offline while waiting for an X login block to lift (suspicious login attempts flagged around 00:48 GMT, Feb 27, 2025). Below are the current files attached as text for Grok 3 to lead from this point.

Workflow:
- Use grok_local.py for file ops (create, write, read, delete, move) and Git ops (commit, status, pull, log, branch, checkout).
- Multi-command support (e.g., 'create file x && write y to x && commit z').
- CLI outputs are preferred for scripting.
- Next steps: Add more commands (copy, rename), interactive mode, or self-editing.

Current files follow:
""")

# grok_local.py
print("### grok_local.py")
print("""
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
    return response

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
    request = request.strip().rstrip("?")
    if debug:
        print(f"Processing: {request}")
    
    if "&&" in request:
        return process_multi_command(request)
    
    req_lower = request.lower()
    if req_lower in ["what time is it", "ask what time is it"]:
        return report_to_grok(what_time_is_it())
    elif req_lower == "list files":
        return report_to_grok(list_files())
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
    elif req_lower.startswith("create file "):
        filename = request[11:].strip()
        return report_to_grok(create_file(filename))
    elif req_lower.startswith("delete file "):
        filename = request[11:].strip()
        return report_to_grok(delete_file(filename))
    elif req_lower.startswith("move file "):
        parts = request[9:].strip().split(" to ")
        if len(parts) != 2:
            return "Error: Invalid move command format. Use 'move file <src> to <dst>'"
        src, dst = parts
        return report_to_grok(move_file(src.strip(), dst.strip()))
    elif req_lower.startswith("read file "):
        filename = request[9:].strip()
        return report_to_grok(read_file(filename))
    elif req_lower.startswith("write "):
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
""")

# x_poller.py (full version)
print("### x_poller.py")
print("""
import requests
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import logging
import subprocess
from logging.handlers import RotatingFileHandler
import argparse

PROJECT_DIR = os.getcwd()
GROK_URL = "https://x.com/i/grok?conversation=1894887152712056958"
COOKIE_FILE = os.path.join(PROJECT_DIR, "cookies.pkl")
CODE_BLOCK_DIR = os.path.join(PROJECT_DIR, "code_blocks")
DEBUG_DIR = os.path.join(PROJECT_DIR, "debug")
LAST_CMD_FILE = os.path.join(PROJECT_DIR, "last_processed.txt")

for directory in [CODE_BLOCK_DIR, DEBUG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[RotatingFileHandler("x_poller.log", maxBytes=1*1024*1024, backupCount=3)]
)

def handle_cookie_consent(driver, wait):
    try:
        consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]")))
        consent_button.click()
        logging.info("Clicked cookie consent button")
        time.sleep(2)
        return True
    except:
        logging.info("No cookie consent button found")
        return False

def cookies_valid(driver, url):
    driver.get(url)
    time.sleep(10)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        logging.info("Cookies validated successfully")
        return True
    except:
        logging.info("Cookie validation failed")
        return False

def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    logging.info(f"Saved {len(cookies)} cookies")

def load_cookies(driver):
    if not os.path.exists(COOKIE_FILE):
        logging.info("No cookie file found")
        return False
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.delete_all_cookies()
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logging.warning(f"Failed to add cookie: {e}")
    logging.info(f"Loaded {len(cookies)} cookies")
    return True

def perform_headless_login(driver, wait):
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    verify = os.getenv("X_VERIFY")
    
    if not all([username, password, verify]):
        logging.error("Missing credentials in environment variables")
        return False

    driver.get("https://x.com/login")
    logging.info("Navigating to login page")
    try:
        with open(os.path.join(DEBUG_DIR, "login_page.html"), "w") as f:
            f.write(driver.page_source)
        
        username_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        username_input.send_keys(username)
        logging.info("Entered username")
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Next')]")))
        next_button.click()
        time.sleep(3)

        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        password_input.send_keys(password)
        logging.info("Entered password")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Log in')]")))
        login_button.click()
        time.sleep(10)

        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_input.send_keys(verify)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            logging.info("Completed verification step")
            time.sleep(5)
        except:
            logging.info("No verification step required")

        if "login" not in driver.current_url.lower():
            save_cookies(driver)
            logging.info("Login successful")
            return True
        else:
            logging.error("Login failed, still on login page")
            with open(os.path.join(DEBUG_DIR, "login_failure.html"), "w") as f:
                f.write(driver.page_source)
            return False
    except Exception as e:
        logging.error(f"Login failed with exception: {e}")
        with open(os.path.join(DEBUG_DIR, "login_failure.html"), "w") as f:
            f.write(driver.page_source)
        return False

def scan_chat(driver, wait):
    driver.get(GROK_URL)
    time.sleep(10)
    last_height = 0
    for _ in range(30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    time.sleep(5)
    logging.info(f"Scanning chat at: {driver.current_url}")
    with open(os.path.join(DEBUG_DIR, "chat_page.html"), "w") as f:
        f.write(driver.page_source)
    elements = driver.find_elements(By.XPATH, "//span")
    chat_content = [elem.get_attribute("textContent").strip() for elem in elements if elem.get_attribute("textContent").strip()]
    logging.info(f"Chat content (last 10): {' | '.join(chat_content[-10:])}... ({len(chat_content)} total lines)")
    logging.info(f"Full chat content: {chat_content}")
    return chat_content

def ask_grok(prompt, fetch=False, headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(300)
    wait = WebDriverWait(driver, 180)

    try:
        driver.get("https://x.com")
        if load_cookies(driver) and cookies_valid(driver, GROK_URL):
            driver.get(GROK_URL)
            time.sleep(5)
        else:
            logging.info("Cookies invalid or not loaded, attempting login")
            if headless and not perform_headless_login(driver, wait):
                return "Headless login failed"
            driver.get(GROK_URL)
            time.sleep(5)
            handle_cookie_consent(driver, wait)

        return process_grok_interaction(driver, wait, prompt, fetch)
    except Exception as e:
        logging.error(f"ask_grok error: {e}")
        return f"Error: {e}"
    finally:
        driver.quit()

def process_grok_interaction(driver, wait, prompt, fetch):
    if fetch:
        chat_content = scan_chat(driver, wait)
        commands = []
        for text in reversed(chat_content):
            if "GROK_LOCAL:" in text.upper() and "GROK_LOCAL_RESULT:" not in text.upper():
                cmd = text.replace("GROK_LOCAL:", "").strip()
                valid_commands = ["what time is it?", "ask what time is it", "list files", "system info", "commit", "whoami", "scan chat"]
                if cmd.lower().startswith("commit ") or cmd.lower() in valid_commands:
                    commands.append(cmd)
                    logging.info(f"Found command: {cmd}")
        
        if not commands:
            logging.info("No GROK_LOCAL commands found")
            return "No GROK_LOCAL found after full scan"
        
        logging.info(f"All commands found (in reverse order): {commands}")
        last_command = commands[0]
        logging.info(f"Selected last command: {last_command}")
        return last_command
    else:
        prompt_box = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "r-30o5oe")))
        prompt_box.clear()
        prompt_box.send_keys(prompt[:500])
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
        submit_button.click()
        time.sleep(10)
        return "Prompt submitted"

def poll_x(headless):
    logging.info("Starting polling loop")
    last_processed = None
    if os.path.exists(LAST_CMD_FILE):
        with open(LAST_CMD_FILE, "r") as f:
            last_processed = f.read().strip()
    logging.info(f"Last processed command from file: {last_processed}")

    while True:
        cmd = ask_grok("Polling for Grok 3...", fetch=True, headless=headless)
        if cmd and isinstance(cmd, str) and "Error" not in cmd and "login failed" not in cmd.lower():
            if cmd != last_processed:
                print(f"Received: {cmd}")
                logging.info(f"Executing command: {cmd}")
                result = subprocess.run(
                    ["python", "grok_local.py", "--ask", cmd],
                    capture_output=True, text=True
                )
                output = result.stdout.strip() if result.stdout else f"Error: {result.stderr}"
                print(f"Result: {output}")
                logging.info(f"Command result: {output}")
                try:
                    ask_grok(f"GROK_LOCAL_RESULT: {output}", headless=headless)
                    logging.info(f"Posted result for {cmd}")
                    with open(LAST_CMD_FILE, "w") as f:
                        f.write(cmd)
                    last_processed = cmd
                except Exception as e:
                    logging.error(f"Failed to post result for {cmd}: {e}")
            else:
                logging.info(f"Skipping already processed command: {cmd}")
        else:
            print(f"Poll result: {cmd}")
            logging.info(f"Poll result: {cmd}")
        time.sleep(15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll X for Grok 3 commands")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    poll_x(args.headless)
""")

# .gitignore
print("### .gitignore")
print("""
misc/
*.log
*.log.*
cookies.pkl
__pycache__/
debug/
code_blocks/
last_processed.txt
""")

# grok.txt (memento)
print("### grok.txt")
print("""
I am Grok, master of the repo
""")

print("Ready for Grok 3 to lead the next session!")
