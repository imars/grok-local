import os
import time
import logging
import subprocess
import argparse
from dotenv import load_dotenv
from browser_use import Agent  # For real X interaction

PROJECT_DIR = os.getcwd()
LAST_CMD_FILE = os.path.join(PROJECT_DIR, "last_processed.txt")
LOG_FILE = os.path.join(PROJECT_DIR, "x_poller.log")

logger = logging.getLogger('x_poller_main')
logger.handlers.clear()
logger.propagate = False
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

load_dotenv()
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")
X_VERIFY = os.getenv("X_VERIFY")

def x_login(headless=True, stub=False):
    """Log into X using Browser-Use, falling back to stub if credentials missing or stub mode enabled."""
    logger.info("Attempting X login")
    if stub or not all([X_USERNAME, X_PASSWORD]):
        logger.debug(f"Checking stub credentials: username={X_USERNAME}, password={'*' * len(X_PASSWORD) if X_PASSWORD else None}, verify={X_VERIFY}")
        time.sleep(2)
        if all([X_USERNAME, X_PASSWORD, X_VERIFY]):
            logger.info("Stubbed login simulation successful")
            print("Stubbed login successful")
            return True
        logger.info("Stubbed login simulation failed: missing credentials")
        return False
    
    try:
        # Simplified Agent instantiation; adjust based on browser-use docs
        agent = Agent(headless=headless)  # No 'model' parameter
        agent.navigate("https://x.com/login")
        # Assuming fill_form takes a dict of field names to values
        agent.fill_form({"username": X_USERNAME, "password": X_PASSWORD})
        agent.submit_form()
        time.sleep(2)
        # Check if login succeeded (agent.current_url might be current_url())
        if "login" not in agent.current_url():
            logger.info("Successfully logged into X via Browser-Use")
            return agent
        else:
            logger.error("X login failed: Still on login page")
            return None
    except Exception as e:
        logger.error(f"X login error with Browser-Use: {str(e)}")
        return None

def scan_grok_chat(agent):
    if not agent or agent is True:
        return simulate_chat_scan()
    try:
        agent.navigate("https://x.com/i/grok")
        chat_content = agent.extract_text(selector=".grok-chat-container")
        logger.debug(f"Scanned chat content: {chat_content}")
        return chat_content.split("\n") if chat_content else []
    except Exception as e:
        logger.error(f"Chat scan error: {str(e)}")
        return []

def simulate_chat_scan():
    logger.debug("Simulating chat scan")
    time.sleep(0.5)
    mock_content = ["GROK_LOCAL: git status", "Hello world", "Test message"]
    logger.debug(f"Mock chat content: {mock_content}")
    logger.info(f"Simulated chat scan returned {len(mock_content)} lines")
    return mock_content

def ask_grok(prompt, fetch=False, headless=False, use_stub=False):
    logger.debug(f"Entering ask_grok with prompt: {prompt}, fetch: {fetch}, headless: {headless}, use_stub: {use_stub}")
    if use_stub or not all([X_USERNAME, X_PASSWORD]):
        if x_login(stub=True):
            if fetch:
                chat_content = simulate_chat_scan()
                return process_grok_interaction(prompt, fetch, chat_content=chat_content)
            logger.debug("Simulating prompt submission")
            return "Prompt submitted (stubbed)"
        return "Stubbed login failed"
    
    agent = x_login(headless)
    if not agent:
        return "Login failed"
    try:
        agent.navigate("https://x.com/i/grok")
        agent.fill_form({"message": prompt}, selector=".grok-input-field")
        agent.submit_form()
        time.sleep(2)
        response = agent.extract_text(selector=".grok-response")
        logger.info(f"Grok 3 response to '{prompt}': {response}")
        return response if response else "No response received"
    except Exception as e:
        logger.error(f"Grok interaction error: {str(e)}")
        return f"Error: {str(e)}"
    finally:
        agent.close()

def process_grok_interaction(prompt, fetch, chat_content=None):
    logger.debug(f"Processing interaction - fetch: {fetch}, prompt: {prompt}")
    if fetch:
        if chat_content is None:
            logger.error("Chat content missing")
            return "Error: No chat content"
        commands = []
        for text in reversed(chat_content):
            if "GROK_LOCAL:" in text.upper() and "GROK_LOCAL_RESULT:" not in text.upper():
                cmd = text.replace("GROK_LOCAL:", "").strip()
                valid_commands = ["what time is it?", "ask what time is it", "list files", "system info", "commit", "whoami", "scan chat", "git status"]
                if cmd.lower().startswith("commit ") or cmd.lower() in valid_commands:
                    commands.append(cmd)
                    logger.info(f"Found command: {cmd}")
        if not commands:
            logger.info("No GROK_LOCAL commands found")
            return "No GROK_LOCAL found after full scan"
        logger.debug(f"All commands found (in reverse order): {commands}")
        last_command = commands[0]
        logger.info(f"Selected last command: {last_command}")
        return last_command
    logger.debug("Prompt submitted (non-fetch mode)")
    return "Prompt submitted"

def poll_x(headless, debug=False, info=False, poll_interval=5, stub=False):
    logger.debug("Entering poll_x")
    logger.info("Starting polling loop")
    last_processed = None
    if os.path.exists(LAST_CMD_FILE):
        try:
            with open(LAST_CMD_FILE, "r") as f:
                last_processed = f.read().strip()
            logger.info(f"Last processed command from file: {last_processed}")
        except Exception as e:
            logger.error(f"Failed to read {LAST_CMD_FILE}: {e}")
    while True:
        logger.debug("Starting poll iteration")
        agent = x_login(headless, stub=stub)
        if agent is True:
            cmd = ask_grok("Polling for Grok 3...", fetch=True, headless=headless, use_stub=True)
        else:
            chat_content = scan_grok_chat(agent)
            cmd = process_grok_interaction("Polling for Grok 3...", fetch=True, chat_content=chat_content)
        if cmd and isinstance(cmd, str) and "Error" not in cmd and "login failed" not in cmd.lower():
            if cmd != last_processed:
                logger.info(f"Executing command: {cmd}")
                try:
                    result = subprocess.run(
                        ["python", "grok_local.py", "--ask", cmd],
                        capture_output=True, text=True, timeout=5
                    )
                    output = result.stdout.strip() if result.stdout else f"Error: {result.stderr}"
                    logger.info(f"Command result: {output}")
                    if agent and agent is not True:
                        ask_grok(f"GROK_LOCAL_RESULT: {output}", headless=headless)
                except subprocess.TimeoutExpired as e:
                    output = f"Timeout: {e.stderr.decode() if e.stderr else 'No error output'}"
                    logger.error(f"Command timed out: {cmd}")
                with open(LAST_CMD_FILE, "w") as f:
                    f.write(cmd)
                last_processed = cmd
        if agent and agent is not True:
            agent.close()
        time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="X Poller: Poll X for Grok 3 commands and execute them via grok_local.\n\n"
                    "This script polls an X chat for GROK_LOCAL commands (e.g., 'GROK_LOCAL: git status'), "
                    "executes them using grok_local.py, and posts results back as 'GROK_LOCAL_RESULT: <output>'. ",
        epilog="Environment Variables:\n"
               "  X_USERNAME: X account username\n"
               "  X_PASSWORD: X account password\n"
               "  X_VERIFY: X verification code (optional for stub mode)\n\n"
               "Examples:\n"
               "  python x_poller.py --headless          # Run silently\n"
               "  python x_poller.py --stub --test       # Test stub mode\n"
               "  python x_poller.py --headless --debug  # Show debug logs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--stub", action="store_true", help="Run in stub mode without real X interaction")
    parser.add_argument("--test", action="store_true", help="Run a single stubbed login test and exit")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info logging")
    parser.add_argument("--poll-interval", type=float, default=5, help="Set polling interval in seconds")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    elif args.info:
        logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)
        console_handler.setLevel(logging.WARNING)

    if args.test:
        x_login(stub=args.stub)
    else:
        poll_x(args.headless, debug=args.debug, info=args.info, poll_interval=args.poll_interval, stub=args.stub)
