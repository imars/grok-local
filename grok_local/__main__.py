#!/usr/bin/env python3
# grok_local/__main__.py
import logging
from logging.handlers import RotatingFileHandler
import argparse
import sys
import time
import requests

from .config import LOG_FILE, AI_BACKEND, BROWSER_BACKEND
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3), logging.StreamHandler()]
)
logger = logging.getLogger()

from .command_handler import ask_local
from .ai_adapters import get_ai_adapter
from git_ops import get_git_interface

BRIDGE_URL = "http://0.0.0.0:5000"

def post_to_bridge(input_text, req_id):
    """Post a request to grok_bridge.py."""
    payload = {"input": input_text, "id": req_id}
    try:
        response = requests.post(f"{BRIDGE_URL}/channel", json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"Request posted to bridge: {req_id}")
            return True
        logger.error(f"Failed to post to bridge: {response.text}")
        return False
    except requests.RequestException as e:
        logger.error(f"Bridge POST failed: {e}")
        return False

def get_from_bridge(req_id, timeout=30):
    """Fetch a response from grok_bridge.py."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BRIDGE_URL}/get-response?id={req_id}", timeout=5)
            if response.status_code == 200:
                logger.info(f"Response received from bridge for {req_id}: {response.text}")
                return response.text
            logger.debug(f"Waiting for bridge response... ({response.text})")
            time.sleep(2)
        except requests.RequestException as e:
            logger.error(f"Bridge GET failed: {e}")
            time.sleep(2)
    logger.error(f"Timeout waiting for bridge response for {req_id}")
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Grok-Local: A CLI for managing files, Git, and AI interactions.\n\n"
                    "AI backends: STUB, MANUAL, GROK_BROWSER, CHATGPT, DEEPSEEK (set AI_BACKEND env var).\n"
                    "Browser backends: SELENIUM, PLAYWRIGHT, BROWSER_USE (set BROWSER_BACKEND env var).",
        epilog="Examples:\n"
               "  python -m grok_local --stub --ask 'grok tell me a joke'\n"
               "  AI_BACKEND=CHATGPT python -m grok_local --info --ask 'grok tell me a joke'\n"
               "  python -m grok_local --bridge --ask 'What is 2 + 2?'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask", type=str, help="Execute a single command and exit")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info output")
    parser.add_argument("--stub", action="store_true", help="Use stubbed AI and Git operations")
    parser.add_argument("--bridge", action="store_true", help="Use grok_bridge for AI interaction")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Logging level set to DEBUG")
    elif args.info:
        logger.setLevel(logging.INFO)
        logger.debug("Logging level set to INFO")
    else:
        logger.setLevel(logging.WARNING)
        logger.debug("Logging level set to WARNING (default)")

    logger.info("Main logger initialized")

    ai_adapter = get_ai_adapter("STUB" if args.stub else AI_BACKEND)
    git_interface = get_git_interface(use_stub=args.stub)

    if args.ask:
        if args.bridge:
            req_id = f"req-{int(time.time())}"
            if post_to_bridge(args.ask, req_id):
                result = get_from_bridge(req_id)
                if result:
                    print(f"Result: {result}")
                else:
                    print("Failed to get response from bridge")
                    sys.exit(1)
            else:
                print("Failed to post request to bridge")
                sys.exit(1)
        else:
            result = ask_local(args.ask, ai_adapter, git_interface, debug=args.debug)
            print(result)
            if "failed" in result.lower():
                sys.exit(1)
    else:
        try:
            while True:
                cmd = input("Command: ")
                if cmd.lower() == "exit":
                    break
                if args.bridge:
                    req_id = f"req-{int(time.time())}"
                    if post_to_bridge(cmd, req_id):
                        result = get_from_bridge(req_id)
                        if result:
                            print(f"Result: {result}")
                        else:
                            print("Failed to get response from bridge")
                    else:
                        print("Failed to post request to bridge")
                else:
                    result = ask_local(cmd, ai_adapter, git_interface, debug=args.debug)
                    print(result)
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            logger.info("Interactive mode exited via KeyboardInterrupt")

if __name__ == "__main__":
    main()
