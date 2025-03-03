#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import logging
import argparse
from abc import ABC, abstractmethod
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
#
# Current Task (Last Checkpoint, Mar 03, 2025):
# - 

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

CRITICAL_FILES = {
    "grok_local.py": {"purpose": "Core CLI logic", "functions": [("ask_local(...)", "Processes CLI commands")]},
    "file_ops.py": {"purpose": "File ops utilities", "functions": [("list_files()", "Lists files in safe/")]},
    "git_ops.py": {"purpose": "Git ops utilities", "functions": [("git_status()", "Returns git status")]},
    "x_poller.py": {"purpose": "Polls X for commands", "functions": [("poll_x(...)", "Polls X in a loop")]},
    ".gitignore": {"purpose": "Ignores temp files", "functions": []},
    "grok.txt": {"purpose": "Memento file", "functions": []},
    "requirements.txt": {"purpose": "Lists dependencies", "functions": []},
    "bootstrap.py": {"purpose": "Setup script", "functions": []},
    "run_grok_test.py": {"purpose": "Runs workflow tests", "functions": []},
    "README.md": {"purpose": "Main documentation", "functions": []},
    "grok_bootstrap.py": {"purpose": "Restarts chats", "functions": [("generate_prompt(...)", "Creates prompt")]},
    "grok_checkpoint.py": {"purpose": "Manages checkpoints", "functions": [("save_checkpoint(...)", "Saves checkpoint")]},
    "tests/test_grok_local.py": {"purpose": "Unit tests", "functions": []},
    "docs/timeline.md": {"purpose": "Timeline and goals", "functions": []},
    "docs/usage.md": {"purpose": "CLI usage guide", "functions": []},
    "docs/installation.md": {"purpose": "Installation guide", "functions": []},
    "local/x_login_stub.py": {"purpose": "X login stub", "functions": [("x_login()", "Simulates login")]},
    "debug_x_poller.sh": {"purpose": "Debug script", "functions": []}
}

# Git Interface
class GitInterface(ABC):
    @abstractmethod
    def get_file_tree(self):
        pass

class StubGit(GitInterface):
    def get_file_tree(self):
        logger.debug("Returning stubbed Git file tree")
        return "Repository File Tree (stubbed):\n  .gitignore\n  grok_local.py\n  x_poller.py"

class RealGit(GitInterface):
    def get_file_tree(self):
        logger.debug("Fetching real Git file tree")
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True, text=True, check=True
            )
            files = result.stdout.splitlines()
            files.sort()
            tree_lines = []
            for file in files:
                parts = file.split('/')
                indent = "  " * (len(parts) - 1)
                tree_lines.append(f"{indent}{parts[-1]}")
            return "Repository File Tree (tracked and untracked, not ignored):\n" + "\n".join(tree_lines)
        except subprocess.CalledProcessError as e:
            return f"Error generating Git file tree: {e}"
        except Exception as e:
            return f"Unexpected error generating Git file tree: {e}"

def get_git_interface(use_stub=True):
    return StubGit() if use_stub else RealGit()

def dump_critical_files(chat_mode=False):
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

def generate_prompt(git_interface, include_main=False):
    preamble = "The following contains information to help you restart a malfunctioning Grok 3 chat session.\n\n"
    with open(__file__, "r") as f:
        lines = f.readlines()
        header = "".join(lines[7:24])

    agent_bootstrap = "\nAgent Bootstrap:\n- Role: You are Grok, tasked with enhancing Grok-Local. Assist the user in CLI development, outputting code via `cat << 'EOF' > <filename>` for easy application.\n- Interaction: Expect user to apply code and report results. Use checkpoints (checkpoints/) to track tasks and Git (--git flag) to sync progress.\n- Focus: Leverage CRITICAL_FILES functions, prioritize Current Task, and align with Goals.\n"
    
    setup = "\nSetup for New Chat:\n- Clone: `git clone git@github.com:imars/grok-local.git`\n- Enter: `cd grok-local`\n- Env: `python -m venv venv && source venv/bin/activate && pip install gitpython`\n- Deps: `pip install -r requirements.txt` (ensure gitpython is listed)\n- Structure: Root has CLI scripts (grok_local.py, grok_bootstrap.py), `checkpoints/` for checkpoints, `scripts/` for test/task scripts, `docs/` for guides, `local/` for stubs, `tests/` for unit tests.\n- Start: `python grok_local.py` (interactive) or `python grok_local.py --ask 'list files'` (test).\n- Agent Role: I (Grok) assist with CLI dev, outputting code via `cat << 'EOF' > <filename>`. User applies it and reports results.\n"
    
    workflow = "\nCurrent Workflow Details:\n- CLI Development: Grok uses `cat << 'EOF' > <filename>` to output code for easy terminal application (e.g., `cat << 'EOF' > git_ops.py`). Copy-paste into your shell.\n- Interaction: Use grok_local.py interactively (`python grok_local.py`) or with `--ask` for single commands.\n- Debugging: Append `--debug` for verbose logs in grok_local.log.\n- Testing/Tasks: Run scripts from `scripts/` (e.g., `./scripts/test_<feature>.sh`) for tests or multi-step processes.\n"

    checkpoint_file = os.path.join('checkpoints', 'checkpoint.json')
    checkpoint_info = ""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        checkpoint_info += "\nLatest Checkpoint:\n"
        checkpoint_info += f"Description: {checkpoint.get('description', 'N/A')}\n"
        checkpoint_info += f"Timestamp: {checkpoint.get('timestamp', 'N/A')}\n"
        checkpoint_info += f"Current Task: {checkpoint.get('current_task', 'N/A')}\n"
        if 'chat_url' in checkpoint:
            checkpoint_info += f"Current Chat URL: {checkpoint['chat_url']}\n"
        if 'chat_address' in checkpoint:
            checkpoint_info += f"Chat Address: {checkpoint['chat_address']}\n"
        if 'chat_group' in checkpoint:
            checkpoint_info += f"Chat Group: {checkpoint['chat_group']}\n"
        if 'file_content' in checkpoint:
            checkpoint_info += "Checkpointed File Content: Included\n"

    file_summary = "\nCritical Files (Feb 28, 2025):\n"
    for filename, info in sorted(CRITICAL_FILES.items()):
        filepath = os.path.join(PROJECT_DIR, filename) if filename not in {"tests/test_grok_local.py", "docs/timeline.md", "docs/usage.md", "docs/installation.md", "local/x_login_stub.py"} else os.path.join(PROJECT_DIR, *filename.split("/"))
        state = "Exists" if os.path.exists(filepath) else "Missing locally"
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
    
    git_tree = "\n" + git_interface.get_file_tree() + "\n"

    instructions = "\nInstructions:\n- Fetch files from git@github.com:imars/grok-local.git (e.g., `git show HEAD:<filename>`) or local disk.\n- Run `python grok_bootstrap.py --dump` for full contents.\n- Execute tests/tasks from `scripts/` (e.g., `chmod +x scripts/test_<feature>.sh && ./scripts/test_<feature>.sh`).\n"

    prompt = preamble + header + agent_bootstrap + setup + workflow + checkpoint_info + file_summary + git_tree + instructions

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

def start_session(git_interface, debug=False, command=None, dump=False, prompt=False, include_main=False):
    if dump:
        dump_critical_files(chat_mode=False)
        return
    if prompt:
        print(generate_prompt(git_interface, include_main=include_main))
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
    parser = argparse.ArgumentParser(
        description="Grok-Local Bootstrap: Restart Grok 3 dev chat sessions with context.\n\n"
                    "This script generates prompts or dumps critical files to restart chat sessions, "
                    "or runs grok_local.py commands. Use --prompt to see the latest checkpoint and file states.",
        epilog="Options:\n"
               "  --debug             Run grok_local.py in debug mode with verbose logs\n"
               "  --command '<cmd>'   Execute '<cmd>' via grok_local.py (e.g., 'list files')\n"
               "  --dump              Dump current contents of critical files\n"
               "  --prompt            Generate a chat restart prompt with checkpoint and file info\n"
               "  --include-main      Include grok_local.py content in the prompt (requires --prompt)\n"
               "  --stub              Use stubbed Git operations instead of real Git\n\n"
               "Examples:\n"
               "  python grok_bootstrap.py --dump          # Dump critical file contents\n"
               "  python grok_bootstrap.py --stub --prompt # Show stubbed prompt with checkpoint\n"
               "  python grok_bootstrap.py --command 'list files'  # Run a command via grok_local.py\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--command", type=str, help="Run a specific command non-interactively")
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files")
    parser.add_argument("--prompt", action="store_true", help="Generate an efficient chat prompt")
    parser.add_argument("--include-main", action="store_true", help="Include grok_local.py in prompt")
    parser.add_argument("--stub", action="store_true", help="Use stubbed Git file tree instead of real Git")
    args = parser.parse_args()

    if args.include_main and not args.prompt:
        logger.warning("--include-main requires --prompt; ignoring --include-main")
        args.include_main = False

    git_interface = get_git_interface(use_stub=args.stub)
    start_session(git_interface, debug=args.debug, command=args.command, dump=args.dump, prompt=args.prompt, include_main=args.include_main)
