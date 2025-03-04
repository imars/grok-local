#!/usr/bin/env python3
# grok_local/__main__.py
import logging
from logging.handlers import RotatingFileHandler
import argparse
import sys

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

def main():
    parser = argparse.ArgumentParser(
        description="Grok-Local: A CLI for managing files, Git, and AI interactions.\n\n"
                    "AI backends: STUB, MANUAL, GROK_BROWSER, CHATGPT, DEEPSEEK (set AI_BACKEND env var).\n"
                    "Browser backends: SELENIUM, PLAYWRIGHT, BROWSER_USE (set BROWSER_BACKEND env var).",
        epilog="Examples:\n"
               "  python -m grok_local --stub --ask 'grok tell me a joke'\n"
               "  AI_BACKEND=CHATGPT python -m grok_local --info --ask 'grok tell me a joke'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask", type=str, help="Execute a single command and exit")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    parser.add_argument("--info", "-i", action="store_true", help="Enable info output")
    parser.add_argument("--stub", action="store_true", help="Use stubbed AI and Git operations")
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
                result = ask_local(cmd, ai_adapter, git_interface, debug=args.debug)
                print(result)
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            logger.info("Interactive mode exited via KeyboardInterrupt")

if __name__ == "__main__":
    main()
