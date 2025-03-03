import os
import time
import logging
import subprocess
import argparse
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

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

class XInterface(ABC):
    @abstractmethod
    def login(self, headless=True):
        pass

    @abstractmethod
    def scan_chat(self):
        pass

    @abstractmethod
    def send_prompt(self, prompt):
        pass

class StubX(XInterface):
    def login(self, headless=True):
        logger.info("Attempting stubbed X login simulation")
        username = os.getenv("X_USERNAME")
        password = os.getenv("X_PASSWORD")
        verify = os.getenv("X_VERIFY")
        logger.debug(f"Checking credentials: username={username}, password={'*' * len(password) if password else None}, verify={verify}")
        time.sleep(2)
        if all([username, password, verify]):
            logger.info("Stubbed login simulation successful")
            return self
        logger.info("Stubbed login simulation failed: missing credentials")
        return None

    def scan_chat(self):
        logger.debug("Simulating chat scan")
        time.sleep(0.5)
        mock_content = ["GROK_LOCAL: git status", "Hello world", "Test message"]
        logger.debug(f"Mock chat content: {mock_content}")
        logger.info(f"Simulated chat scan returned {len(mock_content)} lines")
        return mock_content

    def send_prompt(self, prompt):
        logger.debug(f"Simulating prompt submission: {prompt}")
        return "Prompt submitted (stubbed)"

class RealX(XInterface):
    def __init__(self):
        try:
            from browser_use import Browser
            self.AgentClass = Browser
        except ImportError as e:
            logger.error(f"Browser-Use import failed: {e}")
            raise

    def login(self, headless=True):
        logger.info("Attempting real X login")
        username = os.getenv("X_USERNAME")
        password = os.getenv("X_PASSWORD")
        if not all([username, password]):
            logger.error("Missing X_USERNAME or X_PASSWORD")
            return None
        try:
            self.agent = self.AgentClass(headless=headless)  # Removed 'model' parameter
            self.agent.navigate("https://x.com/login")
            self.agent.fill_form({"username": username, "password": password})
            self.agent.submit_form()
            time.sleep(2)
            if "login" not in self.agent.current_url():
                logger.info("X login successful")
                return self
            logger.error("X login failed: Still on login page")
            return None
        except Exception as e:
            logger.error(f"X login error: {str(e)}")
            return None

    def scan_chat(self):
        if not hasattr(self, 'agent') or not self.agent:
            logger.error("No agent available for chat scan")
            return []
        try:
            self.agent.navigate("https://x.com/i/grok?conversation=1896421056694370460")
            chat_content = self.agent.extract_text(selector=".grok-chat-container")
            logger.debug(f"Scanned chat content: {chat_content}")
            return chat_content.split("\n") if chat_content else []
        except Exception as e:
            logger.error(f"Chat scan error: {str(e)}")
            return []

    def send_prompt(self, prompt):
        if not hasattr(self, 'agent') or not self.agent:
            logger.error("No agent available to send prompt")
            return "Error: No agent"
        try:
            self.agent.navigate("https://x.com/i/grok?conversation=1896421056694370460")
            self.agent.fill_form({"message": prompt}, selector=".grok-input-field")
            self.agent.submit_form()
            time.sleep(2)
            response = self.agent.extract_text(selector=".grok-response")
            logger.info(f"Grok 3 response to '{prompt}': {response}")
            return response if response else "No response received"
        except Exception as e:
            logger.error(f"Prompt send error: {str(e)}")
            return f"Error: {str(e)}"

    def close(self):
        if hasattr(self, 'agent') and self.agent:
            self.agent.close()

def get_x_interface(use_stub=True):
    return StubX() if use_stub else RealX()

def ask_grok(x_interface, prompt, fetch=False, headless=False):
    logger.debug(f"Entering ask_grok with prompt: {prompt}, fetch: {fetch}, headless: {headless}")
    agent = x_interface.login(headless)
    if not agent:
        return "Login failed"
    if fetch:
        chat_content = x_interface.scan_chat()
        return process_grok_interaction(prompt, fetch, chat_content)
    response = x_interface.send_prompt(prompt)
    if isinstance(agent, RealX):
        agent.close()
    return response

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
        return commands[0]
    return "Prompt submitted"

def poll_x(x_interface, headless, debug=False, info=False, poll_interval=5):
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
        cmd = ask_grok(x_interface, "Polling for Grok 3...", fetch=True, headless=headless)
        logger.debug(f"Poll returned: {cmd}")
        if cmd and isinstance(cmd, str) and "Error" not in cmd and "login failed" not in cmd.lower():
            if cmd != last_processed:
                logger.info(f"Executing command: {cmd}")
                try:
                    result = subprocess.run(
                        ["python", os.path.join(PROJECT_DIR, "grok_local.py"), "--ask", cmd],
                        capture_output=True, text=True, timeout=5
                    )
                    output = result.stdout.strip() if result.stdout else f"Error: {result.stderr}"
                    logger.info(f"Command result: {output}")
                    ask_grok(x_interface, f"GROK_LOCAL_RESULT: {output}", headless=headless)
                    logger.info(f"Posted result for {cmd}")
                    with open(LAST_CMD_FILE, "w") as f:
                        f.write(cmd)
                    last_processed = cmd
                except subprocess.TimeoutExpired as e:
                    output = f"Timeout: {e.stderr.decode() if e.stderr else 'No error output'}"
                    logger.error(f"Command timed out: {cmd}")
            else:
                logger.info(f"Skipping already processed command: {cmd}")
        else:
            logger.info(f"Poll result: {cmd}")
        logger.debug(f"Sleeping for {poll_interval} seconds")
        time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="X Poller: Poll X for Grok 3 commands and execute them via grok_local.\n\n"
                    "This script polls an X chat for GROK_LOCAL commands (e.g., 'GROK_LOCAL: git status'), "
                    "executes them using grok_local.py, and posts results back as 'GROK_LOCAL_RESULT: <output>'. "
                    "Supports stubbed mode for testing or real X polling with Browser-Use.",
        epilog="Environment Variables:\n"
               "  X_USERNAME: X account username (required for real mode)\n"
               "  X_PASSWORD: X account password (required for real mode)\n"
               "  X_VERIFY: X verification code (optional for stub mode)\n\n"
               "Examples:\n"
               "  python x_poller.py --stub --debug        # Test with stubs and debug logs\n"
               "  python x_poller.py --headless --info     # Run real polling silently with info logs\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (real mode only)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info logging")
    parser.add_argument("--poll-interval", type=float, default=5, help="Set polling interval in seconds (default: 5)")
    parser.add_argument("--stub", action="store_true", help="Use stubbed mode instead of real X polling")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        logger.debug("Starting x_poller.py with debug mode")
    elif args.info:
        logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
        logger.info("Starting x_poller.py with info mode")
    else:
        logger.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)
        console_handler.setLevel(logging.WARNING)
        logger.info("Starting x_poller.py in silent mode")

    x_interface = get_x_interface(use_stub=args.stub)
    poll_x(x_interface, args.headless, debug=args.debug, info=args.info, poll_interval=args.poll_interval)
