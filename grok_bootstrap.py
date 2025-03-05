#!/usr/bin/env python3
# grok_bootstrap.py (in repo root)
import os
import sys
import subprocess
import json
import logging
import argparse
from logging.handlers import RotatingFileHandler
from git_ops import get_git_interface
from datetime import datetime

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

logger = logging.getLogger(__name__)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logging.getLogger('git_ops').setLevel(logging.INFO)

CRITICAL_FILES = {
    "grok_local.py": {"purpose": "Core CLI logic (legacy)", "functions": [("ask_local(...)", "Processes CLI commands")]},
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
    "debug_x_poller.sh": {"purpose": "Debug script", "functions": []},
    "grok_local/__main__.py": {"purpose": "Main CLI entry point", "functions": [("main(...)", "Handles CLI commands")]},
    "grok_local/ai_adapters/__init__.py": {"purpose": "AI adapters package init", "functions": []},
    "grok_local/ai_adapters/chatgpt_ai.py": {"purpose": "ChatGPT AI adapter", "functions": []},
    "grok_local/ai_adapters/grok_browser_ai.py": {"purpose": "Grok browser AI adapter", "functions": []},
    "grok_local/ai_adapters/manual_ai.py": {"purpose": "Manual AI adapter", "functions": []},
    "grok_local/ai_adapters/deepseek_ai.py": {"purpose": "DeepSeek AI adapter", "functions": [("delegate(...)", "Sends requests to DeepSeek API")]},
    "grok_local/ai_adapters/local_deepseek_ai.py": {"purpose": "Local DeepSeek AI adapter", "functions": []},
    "grok_local/ai_adapters/stub_ai.py": {"purpose": "Stub AI adapter", "functions": []},
    "grok_local/dom_discovery/__init__.py": {"purpose": "DOM discovery package init", "functions": []},
    "grok_local/dom_discovery/__main__.py": {"purpose": "DOM discovery CLI entry", "functions": [("main()", "Runs DOM discovery")]},
    "grok_local/dom_discovery/agent_analyzer.py": {"purpose": "Analyzes DOM elements", "functions": [("analyze_elements(...)", "Identifies navigation roles")]},
    "grok_local/dom_discovery/element_parser.py": {"purpose": "Parses DOM elements", "functions": [("parse_dom_elements(...)", "Extracts elements to JSON")]},
    "grok_local/dom_discovery/html_fetcher.py": {"purpose": "Fetches HTML content", "functions": [("fetch_html(...)", "Loads HTML from file")]},
    "grok_local/dom_discovery/ollama_manager.py": {"purpose": "Manages Ollama AI (stub)", "functions": [("analyze(...)", "Placeholder for analysis")]}
}

def dump_critical_files(chat_mode=False):
    if chat_mode:
        print("Please analyze the project files in the current directory.\n")
    print("=== Critical Files (Feb 28, 2025) ===\n")
    for filename in sorted(CRITICAL_FILES.keys()):
        filepath = os.path.join(PROJECT_DIR, filename)
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

def get_recent_files(num_files=5):
    """Return a list of the most recently modified files with their timestamps."""
    all_files = []
    for root, _, files in os.walk(PROJECT_DIR):
        if 'venv' in root or '__pycache__' in root:
            continue
        for fname in files:
            filepath = os.path.join(root, fname)
            mtime = os.path.getmtime(filepath)
            all_files.append((filepath, mtime))
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    recent_files = all_files[:num_files]
    
    return [(os.path.relpath(fpath, PROJECT_DIR), datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')) 
            for fpath, mtime in recent_files]

def generate_prompt(git_interface, include_main=False, most_recent=None):
    preamble = (
        "The following contains information to help you restart a malfunctioning Grok 3 chat session. "
        "We are currently developing grok_local/dom_discovery/ and grok_local/ai_adapters/, tools to "
        "empower grok_local to discover important DOM elements for navigation by our agent on websites. "
        "Our DeepSeekAI adapter can now analyze downloaded websites in structure to further the goal "
        "of autonomous website harnessing.\n\n"
    )
    header = (
        "# Grok-Local Bootstrap Script (Mar 04, 2025): Restarts dev chat sessions with context.\n"
        "# - Options: --dump (full file contents), --prompt (chat-ready summary), or run python -m grok_local directly.\n"
        "#\n"
        "# Meta (How to Update grok_bootstrap.py):\n"
        "# - When: Update if chat slows (>5s lag), new files/features emerge, or project structure shifts (e.g., new dirs).\n"
        "# - How: 1) Run `--dump` to inspect file states; 2) Add new critical files to CRITICAL_FILES; 3) Refresh Mission,\n"
        "#   Recent Work, Goals, and Workflow with latest from README.md/git log; 4) Test `--prompt` for clarity;\n"
        "#   5) Commit via `python -m grok_local --ask \"commit 'Updated grok_bootstrap for <reason>'\"`.\n"
        "#\n"
        "# Mission Statement:\n"
        "# Grok-Local aims to become a fully autonomous local agent, managing project files and Git repos,\n"
        "# communicating with users and multiple agents (local/remote), and solving problems collaboratively.\n"
        "# Progress: Robust CLI (grok_local/__main__.py, run as `python -m grok_local`) with file/Git ops,\n"
        "# checkpointing system (grok_checkpoint.py), X polling stubs (x_poller.py), and slimmed bootstrap script (~150 lines).\n"
        "#\n"
        "# Recent Work (Feb 28, 2025):\n"
        "# - Slimmed this script from thousands to ~150 lines, removing embedded files.\n"
        "# - Moved checkpoint logic to grok_checkpoint.py, added list/save functionality.\n"
        "# - Integrated x_login_stub.py into x_poller.py for stubbed X polling.\n"
        "#\n"
        "# Goals:\n"
        "# - Short-Term (Mar 2025): Enhance --help across scripts, harden git_commit_and_push with retries.\n"
        "# - Mid-Term (Apr-May 2025): Improve checkpoint listing (metadata), add restore functionality.\n"
        "# - Long-Term (Jun 2025+): Implement real X polling, enable multi-agent communication via Grok 3.\n"
        "#\n"
        "# Current Task (Last Checkpoint, Mar 04, 2025):\n"
        "# -\n"
    )

    agent_bootstrap = (
        "\nAgent Bootstrap:\n"
        "- Role: You are Grok, tasked with enhancing Grok-Local. Assist the user in CLI development, "
        "outputting code via `cat << 'EOF' > <filename>` for easy application.\n"
        "- Interaction: Expect user to apply code and report results. Use checkpoints (checkpoints/) "
        "to track tasks and Git (--git flag) to sync progress.\n"
        "- Focus: Leverage CRITICAL_FILES functions, prioritize Current Task, and align with Goals.\n"
    )

    setup = (
        "\nSetup for New Chat:\n"
        "- Clone: `git clone git@github.com:imars/grok-local.git`\n"
        "- Enter: `cd grok_local`\n"
        "- Env: `python -m venv venv && source venv/bin/activate && pip install gitpython`\n"
        "- Deps: `pip install -r requirements.txt` (ensure gitpython is listed)\n"
        "- Structure: Root has CLI entry (grok_local/__main__.py), grok_bootstrap.py, `checkpoints/` at repo root, "
        "`scripts/` for test/task scripts, `docs/` for guides, `local/` for stubs, `tests/` for unit tests.\n"
        "- Start: `python -m grok_local` (interactive) or `python -m grok_local --ask 'list files'` (test).\n"
        "- Agent Role: I (Grok) assist with CLI dev, outputting code via `cat << 'EOF' > <filename>`. "
        "User applies it and reports results.\n"
    )

    workflow = (
        "\nCurrent Workflow Details:\n"
        "- CLI Development: Grok uses `cat << 'EOF' > <filename>` to output code for easy terminal "
        "application (e.g., `cat << 'EOF' > git_ops.py`). Copy-paste into your shell.\n"
        "- Interaction: Use `python -m grok_local` interactively or with `--ask` for single commands.\n"
        "- Debugging: Append `--debug` for verbose logs in grok_local.log.\n"
        "- Testing/Tasks: Run scripts from `scripts/` (e.g., `./scripts/test_<feature>.sh`) for tests "
        "or multi-step processes.\n"
    )

    checkpoint_file = os.path.join(PROJECT_DIR, 'checkpoints', 'checkpoint.json')
    checkpoint_info = ""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        checkpoint_info += "\nLatest Checkpoint Task:\n"
        desc = checkpoint.get('description', 'No task description available')
        timestamp = checkpoint.get('timestamp', 'Unknown timestamp')
        checkpoint_info += f"- {desc} (Timestamp: {timestamp})\n"
    else:
        checkpoint_info += "\nLatest Checkpoint Task:\n- No checkpoint found\n"

    file_summary = "\nCritical Files (Feb 28, 2025):\n"
    for filename, info in sorted(CRITICAL_FILES.items()):
        filepath = os.path.join(PROJECT_DIR, filename)
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

    recent_files_section = ""
    recent_files_content = ""
    if most_recent is not None:
        num_files = int(most_recent) if most_recent else 5
        recent_files = get_recent_files(num_files)
        recent_files_section = "\nMost Recently Edited Files:\n"
        for filepath, mtime in recent_files:
            recent_files_section += f"- {filepath} (Modified: {mtime})\n"
        
        recent_files_content = "\nContents of Recent Files:\n"
        for filepath, mtime in recent_files:
            recent_files_content += f"\n--- {filepath} (Modified: {mtime}) ---\n"
            try:
                with open(os.path.join(PROJECT_DIR, filepath), 'r') as f:
                    content = f.read()
                    recent_files_content += f"{content}\n"
            except Exception as e:
                recent_files_content += f"# Error reading {filepath}: {e}\n"

    merge_instructions = (
        "\nInstructions for New Agents:\n"
        "- You start with no knowledge of file contents. Any files you generate (e.g., via "
        "`cat << 'EOF' > <filename>`) must be merged with the existing repo at "
        "git@github.com:imars/grok-local.git. Steps:\n"
        "  1. Fetch the latest repo: `git pull origin main`\n"
        "  2. Check if the file exists (e.g., `ls <filename>`). If it does, manually merge your "
        "changes with the existing content. If not, create the new file.\n"
        "  3. Commit your changes: `git add <filename> && git commit -m 'Merged <filename> from "
        "bootstrap'`\n"
        "  4. Push to the repo: `git push origin main`\n"
        "- Use `git diff` or a text editor to resolve conflicts if needed.\n"
    )

    instructions = (
        "\nAdditional Instructions:\n"
        "- Fetch files from git@github.com:imars/grok-local.git (e.g., `git show HEAD:<filename>`).\n"
        "- Run `python grok_bootstrap.py --dump` for full contents.\n"
        "- Execute tests/tasks from `scripts/` (e.g., `chmod +x scripts/test_<feature>.sh && "
        "./scripts/test_<feature>.sh`).\n"
    )

    prompt = (
        preamble + header + agent_bootstrap + setup + workflow + 
        checkpoint_info + file_summary + git_tree + 
        recent_files_section + merge_instructions + instructions + 
        recent_files_content
    )

    if include_main:
        prompt += "\nMain File (grok_local/__main__.py):\n```\n"
        try:
            with open(os.path.join(PROJECT_DIR, "grok_local/__main__.py"), "r") as f:
                prompt += f.read()
        except FileNotFoundError:
            prompt += "# Not found locally, fetch from Git"
        prompt += "\n```\nAgent: Extrapolate as needed."

    logger.info("Generated efficient prompt for chat restart")
    return prompt

def start_session(git_interface, debug=False, command=None, dump=False, prompt=False, include_main=False, most_recent=None):
    # Set logging level based on mode
    if prompt:
        logger.setLevel(logging.WARNING)  # Suppress INFO and DEBUG for prompt
    else:
        logger.setLevel(logging.DEBUG)  # Normal logging for other modes

    if dump:
        dump_critical_files(chat_mode=False)
        return
    if prompt:
        print(generate_prompt(git_interface, include_main=include_main, most_recent=most_recent))
        return

    cmd = [sys.executable, "-m", "grok_local"]
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
                    "Generates prompts or dumps files to restart sessions, or runs python -m grok_local commands. "
                    "Supports stubbed mode for Git operations.",
        epilog="Options:\n"
               "  --debug             Run python -m grok_local in debug mode with verbose logs\n"
               "  --command '<cmd>'   Execute '<cmd>' via python -m grok_local (e.g., 'list files')\n"
               "  --dump              Dump current contents of critical files\n"
               "  --prompt            Generate a chat restart prompt with checkpoint and file info (no logs)\n"
               "  --include-main      Include grok_local/__main__.py in the prompt (requires --prompt)\n"
               "  --most-recent [N]   Include N most recently edited files in prompt (requires --prompt, default 5)\n"
               "  --stub              Use stubbed Git operations instead of real Git\n\n"
               "Examples:\n"
               "  python grok_bootstrap.py --dump          # Dump critical file contents\n"
               "  python grok_bootstrap.py --prompt --most-recent 3  # Show prompt with 3 recent files\n"
               "  python grok_bootstrap.py --command 'list files'  # Run a command via grok_local\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--command", type=str, help="Run a specific command non-interactively")
    parser.add_argument("--dump", action="store_true", help="Dump current contents of critical files")
    parser.add_argument("--prompt", action="store_true", help="Generate an efficient chat prompt")
    parser.add_argument("--include-main", action="store_true", help="Include grok_local/__main__.py in prompt")
    parser.add_argument("--most-recent", nargs='?', const="5", type=str, help="Include N most recent files in prompt (default 5)")
    parser.add_argument("--stub", action="store_true", help="Use stubbed Git file tree instead of real Git")
    args = parser.parse_args()

    if args.include_main and not args.prompt:
        logger.warning("--include-main requires --prompt; ignoring --include-main")
        args.include_main = False
    if args.most_recent and not args.prompt:
        logger.warning("--most-recent requires --prompt; ignoring --most-recent")
        args.most_recent = None

    git_interface = get_git_interface(use_stub=args.stub)
    start_session(git_interface, debug=args.debug, command=args.command, dump=args.dump, 
                  prompt=args.prompt, include_main=args.include_main, most_recent=args.most_recent)
