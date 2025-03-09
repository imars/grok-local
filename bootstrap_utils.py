import os
import datetime
import subprocess
import json
from agent_config import AGENT_SECTION

# Critical files to include in prompt (updated Mar 09, 2025)
CRITICAL_FILES = [
    "grok_local/__main__.py",
    "grok_local/command_handler.py",
    "grok_local/grok_bridge.py",
    "grok_local/commands/__init__.py",
    "grok_local/commands/git_commands.py",
    "grok_local/commands/file_commands.py",
    "grok_local/commands/bridge_commands.py",
    "grok_local/commands/checkpoint_commands.py",
    "grok_local/commands/misc_commands.py",
    "grok_local/tools/__init__.py",
    "grok_local/tools/config.py",
    "grok_local/tools/logging.py",
    "scripts/test_bridge_e2e.sh",
    "grok_checkpoint.py",
    "git_ops.py",
    "file_ops.py",
    "grok_bootstrap.py",
    "bootstrap_utils.py",
    "agent_config.py",
    "recent_files_fallback.json"
]

# File to store the last used LLM
LAST_LLM_FILE = ".last_llm"
# File for static recent files fallback
RECENT_FILES_JSON = "recent_files_fallback.json"

def get_last_llm():
    """Retrieve the last used LLM from the .last_llm file, or return default if not found."""
    try:
        if os.path.exists(LAST_LLM_FILE):
            with open(LAST_LLM_FILE, 'r') as f:
                last_llm = f.read().strip()
                if last_llm:
                    return last_llm
    except Exception as e:
        print(f"Warning: Could not read {LAST_LLM_FILE}: {e}", file=sys.stderr)
    return "Unknown LLM, origin unspecified"

def save_last_llm(llm):
    """Save the specified LLM to the .last_llm file."""
    try:
        with open(LAST_LLM_FILE, 'w') as f:
            f.write(llm)
    except Exception as e:
        print(f"Warning: Could not write to {LAST_LLM_FILE}: {e}", file=sys.stderr)

def get_recent_files(use_static=False):
    """Get a list of recently changed files, using JSON fallback if specified or Git fails."""
    if use_static:
        try:
            with open(RECENT_FILES_JSON, 'r') as f:
                files = json.load(f)
            print(f"Using static recent files from {RECENT_FILES_JSON}.", file=sys.stderr)
            return [f for f in files if f and os.path.exists(f)]
        except Exception as e:
            print(f"Warning: Failed to load {RECENT_FILES_JSON}: {e}, scanning filesystem instead.", file=sys.stderr)

    try:
        cmd = ["git", "log", "--since=1.day", "--name-only", "--pretty=format:"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = set(result.stdout.splitlines())
        return [f for f in files if f and os.path.exists(f)]
    except subprocess.CalledProcessError:
        print("Warning: Failed to fetch recent files from Git, scanning local filesystem.", file=sys.stderr)
        recent_files = []
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        for root, dirs, files in os.walk(".", topdown=True):
            if "__pycache__" in root:
                continue
            for file in files:
                path = os.path.join(root, file)
                try:
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    if mod_time > one_day_ago:
                        recent_files.append(path)
                except Exception:
                    continue
        return sorted(recent_files, key=os.path.getmtime, reverse=True)

def generate_prompt(most_recent=False, target_llm="Unknown LLM, origin unspecified", use_static=False):
    """Generate a prompt with context for restarting a dev chat session."""
    preamble = (
        f"The following contains information to restart a chat session for {target_llm} to assist with the development of grok_local. "
        "Grok_local is a CLI agent being enhanced for managing project files, Git repos, and agent communication. "
        "It uses a modular command structure and local inference with various LLMs (e.g., via Ollama or a bridge). "
        "Grok_local is not affiliated with any specific LLM provider but can leverage models like Grok (created by xAI), "
        "LLaMA, or others. The goal is for the specified LLM to provide tailored development support for grok_local, "
        f"identifying itself as '{target_llm}' and leveraging its unique capabilities.\n\n"
    )
    prompt = preamble + (
        "# Grok-Local Bootstrap Context (Mar 09, 2025)\n"
        "# Mission: Build a fully autonomous local agent for managing project files, Git repos, "
        "communicating with users and agents, and solving problems collaboratively.\n\n"
        "## Workflow\n"
        "Output files using `cat << EOF ... EOF` to write content directly to the filesystem. "
        "Output commands to be run on the server in syntax-highlighted triple-backtick code blocks "
        "(e.g., ```bash\\n<command>\\n``` for shell commands or ```python\\n<code>\\n``` for Python code). "
        "This ensures clear separation of file writes and executable commands with proper syntax highlighting "
        "for readability in Markdown-compatible environments.\n\n"
        "## Agent\n" + AGENT_SECTION.format(target_llm=target_llm) + "\n"
        "## Progress\n"
        "Modular CLI with direct execution (--do) and local inference via Ollama, bridge for escalation to various LLMs.\n\n"
        "## Recent Work (Mar 09, 2025)\n"
        "- Added --do for direct execution with local inference fallback.\n"
        "- Integrated Ollama for true local inference with deepseek-r1:8b.\n"
        "- Enhanced conversational responses in tools.py.\n"
        "- Fixed tree command imports and made timestamps optional in misc_commands.py.\n"
        "- Updated critical files list and added checkpoint option in grok_bootstrap.py.\n\n"
        "## Critical Files\n"
    )
    for file in CRITICAL_FILES:
        if os.path.exists(file):
            prompt += f"- `{file}`: {os.path.getsize(file)} bytes, last modified {datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            prompt += f"- `{file}`: Missing locally, fetch from Git\n"
    prompt += (
        "\n## Instructions\n"
        "- Use these files to restart dev chats with current context.\n"
        "- Fetch missing files from git@github.com:imars/grok-local.git if needed.\n"
        "- Ensure Ollama is running (`ollama serve`) for local inference.\n\n"
        "## How the LLM Should Respond\n"
        f"The LLM should greet the user as follows: 'Hello! I’m {target_llm}, here to assist with your development of grok_local.' "
        "Summarize the context (Mission, Recent Progress, Next Goals) and offer specific suggestions based on 'Next Goals' "
        "(refine CLI features and explore X polling or DOM discovery), such as:\n"
        "- Refining CLI features: Suggest new commands, improve error handling in `command_handler.py`, optimize model selection in `tools.py`.\n"
        "- Exploring X polling: Generate stubs (e.g., for `misc_commands.py`), provide insights on X polling or DOM discovery if capable.\n"
        "- General development: Checkpoint progress, summarize Git changes, generate/edit code.\n"
        "Ask for a specific command or question (e.g., 'Generate a stub for X polling in `misc_commands.py`.', 'Summarize the latest changes in the `grok_local` repo.'). "
        "Highlight your capabilities: Use grok_local tools, leverage your reasoning or external data access (if available), output files with `cat << EOF`, commands in ```bash blocks.\n"
    )

    if most_recent:
        recent_files = get_recent_files(use_static=use_static)
        prompt += "\n## Recently Changed/Added Files (Mar 09, 2025)\n"
        for file in recent_files:
            if os.path.exists(file):
                # Determine file type for syntax highlighting
                if file.endswith('.py'):
                    lang = 'python'
                elif file.endswith('.sh'):
                    lang = 'bash'
                else:
                    lang = 'text'
                prompt += f"\n### {file}\n```{lang}\n"
                with open(file, 'r') as f:
                    prompt += f.read()
                prompt += "\n```\n"
            else:
                prompt += f"\n### {file}\nMissing locally, fetch from Git\n"

    return prompt

def dump_files():
    """Dump the full contents of critical files to stdout."""
    for file in CRITICAL_FILES:
        if os.path.exists(file):
            print(f"\n# {file}\n")
            with open(file, 'r') as f:
                print(f.read())
        else:
            print(f"\n# {file}\n# Missing locally\n")
