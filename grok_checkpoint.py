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
        args.extend(["--ask", command])
    
    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )
    print(result.stdout.strip())
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if "--resume" in sys.argv:
            start_session(resume=True)
        else:
            start_session(" ".join(sys.argv[1:]))
    else:
        start_session()
