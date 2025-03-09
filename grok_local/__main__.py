import subprocess
import atexit
import argparse
import time
import signal
from .command_handler import CommandHandler  # Updated import
from git_ops import get_git_interface
from .ai_adapters.stub_ai import StubAI

BRIDGE_PROCESS = None

def start_bridge():
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS is None:
        BRIDGE_PROCESS = subprocess.Popen(["python", "grok_local/grok_bridge.py"])
        print("Started grok_bridge at http://0.0.0.0:5000")
        time.sleep(2)

def stop_bridge():
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS and BRIDGE_PROCESS.poll() is None:
        BRIDGE_PROCESS.send_signal(signal.SIGTERM)
        try:
            BRIDGE_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            BRIDGE_PROCESS.kill()
        print("Stopped grok_bridge")
        BRIDGE_PROCESS = None

def main():
    parser = argparse.ArgumentParser(description="Grok-Local CLI: Autonomous agent for file, Git, and agent tasks.")
    parser.add_argument("command", nargs="?", type=str, help="Command to run (e.g., 'checkpoint \"Update\"')")
    parser.add_argument("--do", action="store_true", help="Execute command directly with local inference fallback")
    parser.add_argument("--no-git", action="store_true", help="Disable Git integration (default: enabled)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--model", type=str, choices=["llama3.2:latest", "deepseek-r1:8b", "deepseek-r1:latest"], 
                        help="Override default model selection (default: auto based on command length)")
    args = parser.parse_args()

    git_interface = get_git_interface()
    ai_adapter = StubAI()
    atexit.register(stop_bridge)

    if args.command:
        handler = CommandHandler(git_interface, ai_adapter)
        print(handler.handle([args.command] + ([f"--do={args.do}", "--model={args.model}"] if args.model else [])))
    else:
        print("Interactive mode not implemented yet. Provide a command.")

if __name__ == "__main__":
    main()
