import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

def start_session(command=None, resume=False):
    """Start a grok-local session, either interactive, with a command, or resuming."""
    args = ["python", "grok_local.py"]
    if resume:
        args.append("--resume")
    elif command:
        if command.startswith("--ask "):
            args.append("--ask")
            args.append(command[6:].strip())
        else:
            args.append(command)
    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )
    print(result.stdout.strip())
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grok Checkpoint: Start or resume a grok-local session with checkpointing.",
        epilog="Examples: 'python grok_checkpoint.py --resume' or 'python grok_checkpoint.py --ask \"checkpoint My backup\"'"
    )
    parser.add_argument("--resume", action="store_true", help="Resume from the last checkpoint")
    parser.add_argument("--ask", type=str, help="Run a specific command and exit")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    args = parser.parse_args()

    if args.resume:
        start_session(resume=True)
    elif args.ask:
        start_session(command=f"--ask {args.ask}")
    else:
        start_session()
