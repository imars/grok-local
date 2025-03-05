import subprocess
import atexit
import argparse
import time
from .command_handler import ask_local
from git_ops import get_git_interface
from .ai_adapters.stub_ai import StubAI

BRIDGE_PROCESS = None

def start_bridge():
    global BRIDGE_PROCESS
    BRIDGE_PROCESS = subprocess.Popen(["python", "grok_local/grok_bridge.py"])
    print("Started grok_bridge at http://0.0.0.0:5000")
    time.sleep(2)

def stop_bridge():
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS:
        BRIDGE_PROCESS.terminate()
        BRIDGE_PROCESS.wait()
        print("Stopped grok_bridge")

def main():
    parser = argparse.ArgumentParser(description="Grok-Local CLI: Autonomous agent for file, Git, and agent tasks.")
    parser.add_argument("--ask", type=str, help="Run a command and exit (e.g., 'checkpoint \"Update\" --git')")
    parser.add_argument("--no-git", action="store_true", help="Disable Git integration for commands (default: Git enabled)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    git_interface = get_git_interface()
    ai_adapter = StubAI()
    start_bridge()
    atexit.register(stop_bridge)

    if args.ask:
        print(ask_local(args.ask, ai_adapter, git_interface, args.debug, use_git=not args.no_git))
    else:
        print("Interactive mode not implemented yet. Use --ask.")

if __name__ == "__main__":
    main()
