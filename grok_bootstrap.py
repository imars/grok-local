#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import argparse
from logging.handlers import RotatingFileHandler

# Grok-Local Bootstrap Script (Feb 28, 2025): Restarts dev chat sessions with context.
# - Options: --dump (full file contents), --prompt (chat-ready summary), or run grok_local.py directly.
#
# Meta (How to Update grok_bootstrap.py):
# - When: Update if chat slows (>5s lag), new files/features emerge, or project structure shifts (e.g., new dirs).
# - How: 1) Run `--dump` to inspect file states; 2) Add new critical files to CRITICAL_FILES; 3) Refresh Mission,
#   Recent Work, Goals, and Workflow with latest from README.md/git log; 4) Test `--prompt` for clarity;
#   5) Commit via `python grok_local.py --ask "commit 'Updated grok_bootstrap for <reason>'"`.
#
# Mission Statement:
# Grok-Local aims to become a fully autonomous local agent, managing project files and Git repos,
# communicating with users and multiple agents (local/remote), and solving problems collaboratively.
# Progress: Robust CLI (grok_local.py) with file/Git ops, checkpointing system (grok_checkpoint.py),
# X polling stubs (x_poller.py), and slimmed bootstrap script (~150 lines).
#
# Recent Work (Feb 28, 2025):
# - Slimmed this script from thousands to ~150 lines, removing embedded files.
# - Moved checkpoint logic to grok_checkpoint.py, added list/save functionality.
# - Integrated x_login_stub.py into x_poller.py for stubbed X polling.
#
# Goals:
# - Short-Term (Mar 2025): Enhance --help across scripts, harden git_commit_and_push with retries.
# - Mid-Term (Apr-May 2025): Improve checkpoint listing (metadata), add restore functionality.
# - Long-Term (Jun 2025+): Implement real X polling, enable multi-agent communication via Grok 3.

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CRITICAL_FILES = {
    "grok_local.py": {
        "purpose": "Core CLI logic for file/Git ops and Grok 3 delegation",
        "functions": [
            ("report_to_grok(response: str) -> str", "Returns response for Grok integration"),
            ("what_time_is_it() -> str", "Returns current UTC time as formatted string"),
            ("delegate_to_grok(request: str) -> str", "Sends request to Grok 3, awaits response"),
            ("process_multi_command(request: str) -> str", "Handles multiple commands split by &&"),
            ("ask_local(request: str, debug: bool = False) -> str", "Processes CLI commands")
        ]
    },
    "file_ops.py": {
        "purpose": "File operation utilities (create, delete, move, etc.)",
        "functions": [
            ("create_file(filename: str, path: str = None) -> str", "Creates a new file"),
            ("delete_file(filename: str) -> str", "Deletes a file"),
            ("move_file(src_fname: str, dst_fname: str, src_path: str = None, dst_path: str = None) -> str", "Moves a file"),
            ("copy_file(src: str, dst: str) -> str", "Copies a file"),
            ("read_file(filename: str) -> str", "Reads file contents"),
            ("write_file(filename: str, content: str, path: str = None) -> str", "Writes content to file"),
            ("list_files() -> str", "Lists files in safe/"),
            ("rename_file(src: str, dst: str) -> str", "Renames a file"),
            ("clean_cruft() -> str", "Removes untracked files")
        ]
    },
    "git_ops.py": {
        "purpose": "Git operation utilities (status, commit, push, etc.)",
        "functions": [
            ("git_status() -> str", "Returns git status"),
            ("git_pull() -> str", "Pulls latest changes from remote"),
            ("git_log(count: int = 1) -> str", "Shows last <count> commits"),
            ("git_branch() -> str", "Lists git branches"),
            ("git_checkout(branch: str) -> str", "Switches to specified branch"),
            ("git_rm(filename: str) -> str", "Removes file from Git tracking"),
            ("git_clean_repo() -> str", "Cleans untracked files"),
            ("git_commit_and_push(message: str) -> str", "Commits and pushes changes")
        ]
    },
    "x_poller.py": {
        "purpose": "Polls X for Grok 3 commands, currently stubbed",
        "functions": [
            ("x_login() -> bool", "Simulates X login with env vars"),
            ("simulate_chat_scan() -> list", "Mocks X chat content"),
            ("ask_grok(prompt: str, fetch: bool = False, headless: bool = False, use_stub: bool = True) -> str", "Handles Grok interactions"),
            ("process_grok_interaction(prompt: str, fetch: bool, chat_content: list = None) -> str", "Processes chat commands"),
            ("poll_x(headless: bool, debug: bool = False, info: bool = False, poll_interval: float = 5)", "Polls X in a loop")
        ]
    },
    ".gitignore": {"purpose": "Ignores temp files and dirs for Git", "functions": []},
    "grok.txt": {"purpose": "Simple memento file, purpose unclear", "functions": []},
    "requirements.txt": {"purpose": "Lists project dependencies (e.g., gitpython)", "functions": []},
    "bootstrap.py": {"purpose": "Setup script (placeholder, may be missing)", "functions": []},
    "run_grok_test.py": {"purpose": "Runs mini project workflow tests", "functions": []},
    "README.md": {"purpose": "Main project documentation", "functions": []},
    "grok_bootstrap.py": {
        "purpose": "Restarts dev chat sessions",
        "functions": [
            ("dump_critical_files(chat_mode: bool = False)", "Dumps file contents"),
            ("generate_prompt(include_main: bool = False) -> str", "Creates chat restart prompt"),
            ("start_session(debug: bool = False, command: str = None, dump: bool = False, prompt: bool = False, include_main: bool = False)", "Manages session start")
        ]
    },
    "grok_checkpoint.py": {
        "purpose": "Manages sessions and checkpoints",
        "functions": [
            ("list_checkpoints() -> str", "Lists checkpoint files"),
            ("save_checkpoint(description: str, filename: str = 'checkpoint.json') -> str", "Saves a checkpoint"),
            ("start_session(command: str = None, resume: bool = False) -> str", "Starts or resumes a session")
        ]
    },
    "tests/test_grok_local.py": {"purpose": "Unit tests for grok_local functionality", "functions": []},
    "docs/timeline.md": {"purpose": "Project timeline and goals", "functions": []},
    "docs/usage.md": {"purpose": "Detailed CLI usage guide", "functions": []},
    "docs/installation.md": {"purpose": "Installation instructions", "functions": []},
    "local/x_login_stub.py": {
        "purpose": "Stub for X login simulation",
        "functions": [
            ("x_login() -> bool", "Simulates X login with env vars")
        ]
    },
    "debug_x_poller.sh": {"purpose": "Debug script for x_poller.py", "functions": []}
}

def dump_critical_files(chat_mode=False):
    """Print current contents of critical files from disk for session restart."""
    if chat_mode:
        print("Please analyze the project files in the current directory.\n")
    print("=== Critical Files (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES.keys()):
        filepath = os.path.join(PROJECT_DIR, filename) if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(PROJECT_DIR, *filename.split("/"))
        print(f"--- {filename} ---")
        try:
            with open(filepath, "r") as f:
                print(f.read())
            logger.info(f"Dumped contents of {filename}")
        except FileNotFoundError:
            print(f"# File not found: {filepath} - assumed in Git or placeholder")
            logger.warning(f"Could not find {filename} for dumping")
        except Exception as e:
            print(f"# Error reading {filename}: {e}")
            logger.error(f"Error dumping {filename}: {e}")
        print("\n")
    print("=== End of Critical File Contents ===")

def generate_prompt(include_main=False):
    """Generate an efficient prompt for restarting a chat session."""
    preamble = "The following contains information to help you restart a malfunctioning Grok 3 chat session.\n\n"
    with open(__file__, "r") as f:
        lines = f.readlines()
        header = "".join(lines[7:22])  # Skip shebang and imports, start at description
    
    setup = "\nSetup for New Chat:\n- Clone: `git clone git@github.com:imars/grok-local.git`\n- Enter: `cd grok-local`\n- Env: `python -m venv venv && source venv/bin/activate && pip install gitpython`\n- Deps: `pip install -r requirements.txt` (ensure gitpython is listed)\n- Structure: Root has CLI scripts (grok_local.py, grok_bootstrap.py), `docs/` for guides, `local/` for stubs, `tests/` for unit tests.\n- Start: `python grok_local.py` (interactive) or `python grok_local.py --ask 'list files'` (test).\n- Agent Role: I (Grok) assist with CLI dev, outputting code via `cat << 'EOF' > <filename>`. User applies it and reports results.\n"
    
    workflow = "\nCurrent Workflow Details:\n- CLI Development: Grok uses `cat << 'EOF' > <filename>` to output code for easy terminal application (e.g., `cat << 'EOF' > git_ops.py`). Copy-paste into your shell.\n- Interaction: Use grok_local.py interactively (`python grok_local.py`) or with `--ask` for single commands.\n- Debugging: Append `--debug` for verbose logs in grok_local.log.\n"

    file_summary = "\nCritical Files (Feb 28, 2025):\n"
    for filename, info in sorted(CRITICAL_FILES.items()):
        filepath = filename if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(*filename.split("/"))
        full_path = os.path.join(PROJECT_DIR, filepath)
        state = "Exists" if os.path.exists(full_path) else "Missing locally"
        insights = "Stable Feb 28, 2025"
        if filename == "grok_bootstrap.py":
            insights = "Slimmed to ~150 lines, Feb 28, 2025"
        elif filename == "grok_checkpoint.py":
            insights = "Enhanced with checkpoint funcs, Feb 28, 2025"
        elif filename == "x_poller.py":
            insights = "Stubbed, awaiting real X polling"
        elif state == "Missing locally":
            insights = "Fetch from Git if critical"
        file_summary += f"- {filename} | Location: {filepath} | Purpose: {info['purpose']} | State: {state} | Insights: {insights}\n"
        if info["functions"]:
            file_summary += "  Functions:\n"
            for func_sig, desc in info["functions"]:
                file_summary += f"    - {func_sig}: {desc}\n"

    instructions = "\nInstructions:\n- Fetch files from git@github.com:imars/grok-local.git (e.g., `git show HEAD:<filename>`) or local disk.\n- Run `python grok_bootstrap.py --dump` for full contents.\n"

    prompt = preamble + header + setup + workflow + file_summary + instructions

    if include_main:
        prompt += "\nMain File (grok_local.py):\n```\n"
        try:
            with open(os.path.join(PROJECT_DIR, "grok_local.py"), "r") as f:
                prompt += f.read()
        except FileNotFoundError:
            prompt += "# Not found locally, fetch from Git"
        prompt += "\n```\nAgent: Extrapolate as needed."

    logger.info("Generated efficient prompt for chat restart")
    return prompt

def start_session(debug=False, command=None, dump=False, prompt=False, include_main=False):
    """Start a grok_local session, dump files, or generate a prompt."""
    if dump:
        dump_critical_files(chat_mode=False)
        return
    if prompt:
        print(generate_prompt(include_main=include_main))
        return

    cmd = [sys.executable, os.path.join(PROJECT_DIR, "grok_local.py")]
    if debug:
        cmd.append("--debug")
    if command:
        cmd.extend(["--ask", command])
        logger.info(f"Running non-interactive command: {command}")
    else:
        logger.info("Starting interactive grok_local session...")

    try:
        logger.info("Restarting grok_local dev chat session...")
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if command and result.stdout:
            print(result.stdout)
        if result.stderr:
            logger.error(f"Stderr: {result.stderr}")
        logger.info("Grok_local session completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restart grok_local session: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Session interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restart a Grok Local dev chat session")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--command", type=str, help="Run a specific command non-interactively")
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files")
    parser.add_argument("--prompt", action="store_true", help="Generate an efficient chat prompt")
    parser.add_argument("--include-main", action="store_true", help="Include grok_local.py in prompt")
    args = parser.parse_args()

    if args.include_main and not args.prompt:
        logger.warning("--include-main requires --prompt; ignoring --include-main")
        args.include_main = False

    start_session(debug=args.debug, command=args.command, dump=args.dump, prompt=args.prompt, include_main=args.include_main)
