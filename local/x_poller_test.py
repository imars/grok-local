import os
import time
import logging
import subprocess
import argparse

PROJECT_DIR = os.getcwd()
LAST_CMD_FILE = os.path.join(PROJECT_DIR, "last_processed.txt")
LOG_FILE = os.path.join(PROJECT_DIR, "x_poller.log")

# Setup logging globally with basic handlers
logger = logging.getLogger('x_poller_test')
logger.handlers.clear()
logger.propagate = False
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def x_login():
    """Simulate an X login process using environment variables, adapted from x_login_stub.py."""
    logger.info("Attempting X login simulation")
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    verify = os.getenv("X_VERIFY")
    logger.debug(f"Checking credentials: username={username}, password={'*' * len(password) if password else None}, verify={verify}")
    time.sleep(2)  # Simulate network delay as per x_login_stub.py
    if all([username, password, verify]):
        logger.info("Login simulation successful")
        return True
    logger.info("Login simulation failed: missing credentials")
    return False

def simulate_chat_scan():
    """Simulate scanning an X chat for testing purposes."""
    logger.debug("Simulating chat scan")
    time.sleep(0.5)
    mock_content = ["GROK_LOCAL: git status", "Hello world", "Test message"]
    logger.debug(f"Mock chat content: {mock_content}")
    logger.info(f"Simulated chat scan returned {len(mock_content)} lines")
    return mock_content

def ask_grok(prompt, fetch=False, headless=False, use_stub=True):
    logger.debug(f"Entering ask_grok with prompt: {prompt}, fetch: {fetch}, headless: {headless}, use_stub: {use_stub}")
    if use_stub:
        logger.debug("Using stubbed workflow")
        if x_login():  # Integrated from x_login_stub.py
            logger.info("Stubbed login successful")
            if fetch:
                chat_content = simulate_chat_scan()
                return process_grok_interaction(prompt, fetch, chat_content=chat_content)
            logger.debug("Simulating prompt submission")
            return "Prompt submitted (stubbed)"
        logger.debug("Stubbed login failed")
        return "Stubbed login failed"
    logger.error("Non-stubbed mode not implemented")
    return "Error: Use stub mode for now"

def process_grok_interaction(prompt, fetch, chat_content=None):
    logger.debug(f"Processing interaction - fetch: {fetch}, prompt: {prompt}")
    if fetch:
        if chat_content is None:
            logger.error("Chat content missing in non-stub mode")
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

def poll_x(headless, debug=False, info=False, poll_interval=5):
    logger.debug("Entering poll_x")
    logger.info("Starting polling loop")
    logger.debug(f"Polling with headless: {headless}, debug: {debug}, info: {info}, poll_interval: {poll_interval}")
    last_processed = None
    if os.path.exists(LAST_CMD_FILE):
        try:
            with open(LAST_CMD_FILE, "r") as f:
                last_processed = f.read().strip()
            logger.info(f"Last processed command from file: {last_processed}")
        except Exception as e:
            logger.error(f"Failed to read {LAST_CMD_FILE}: {e}")
    else:
        logger.info("No last_processed.txt found")

    while True:
        logger.debug("Starting poll iteration")
        cmd = ask_grok("Polling for Grok 3...", fetch=True, headless=headless)
        logger.debug(f"Poll returned: {cmd}")
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
                except subprocess.TimeoutExpired as e:
                    output = f"Timeout: {e.stderr.decode() if e.stderr else 'No error output'}"
                    logger.error(f"Command timed out: {cmd}")
                logger.debug(f"Posting result: GROK_LOCAL_RESULT: {output}")
                ask_grok(f"GROK_LOCAL_RESULT: {output}", headless=headless)
                logger.debug("Result posted successfully")
                logger.info(f"Posted result for {cmd}")
                with open(LAST_CMD_FILE, "w") as f:
                    f.write(cmd)
                last_processed = cmd
            else:
                logger.info(f"Skipping already processed command: {cmd}")
        else:
            logger.info(f"Poll result: {cmd}")
        logger.debug(f"Sleeping for {poll_interval} seconds before next iteration")
        time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="X Poller Test: Poll X for Grok 3 commands and execute them via grok_local (testing version).",
        epilog="Requires X_USERNAME, X_PASSWORD, X_VERIFY env vars. Example: 'python local/x_poller_test.py --headless'"
    )
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info logging (default is silent)")
    parser.add_argument("--poll-interval", type=float, default=5, help="Set polling interval in seconds (default: 5)")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        logger.debug("Starting x_poller_test.py with debug mode")
    elif args.info:
        logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
        logger.info("Starting x_poller_test.py with info mode")
    else:
        logger.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)
        console_handler.setLevel(logging.WARNING)
        logger.info("Starting x_poller_test.py in silent mode")

    poll_x(args.headless, debug=args.debug, info=args.info, poll_interval=args.poll_interval)
