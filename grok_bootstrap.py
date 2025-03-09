#!/usr/bin/env python3
# grok_bootstrap.py (Mar 09, 2025): Restarts dev chat sessions with context for a specified LLM to assist with grok_local development.
# Options: --dump (full file contents), --prompt (chat-ready summary to clipboard), --most-recent (summary + recent files to clipboard), 
#          --llm (target LLM), --use-static (use static recent files from JSON), --checkpoint (save progress with message).
# Default (no options): Same as --most-recent, using the last specified LLM from .last_llm or 'Unknown LLM, origin unspecified'.

import argparse
import sys
import subprocess
from bootstrap_utils import get_last_llm, save_last_llm, generate_prompt, dump_files

try:
    import pyperclip
except ImportError:
    print("Warning: pyperclip not installed. Install with 'pip install pyperclip' for clipboard support.", file=sys.stderr)
    pyperclip = None

def run_checkpoint(message, use_git=True):
    """Run grok_checkpoint.py with the given message and optional Git integration."""
    # Format the command to match grok_checkpoint.py's --ask syntax
    cmd = ["python", "grok_checkpoint.py", "--ask", f'checkpoint "{message}"']
    if use_git:
        cmd[-1] += " --git"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Checkpoint failed: {e.stderr}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grok-Local Bootstrap: Restart dev chats with context for a specified LLM's assistance.")
    parser.add_argument("--dump", action="store_true", help="Dump full contents of critical files.")
    parser.add_argument("--prompt", action="store_true", help="Generate chat-ready summary and copy to clipboard.")
    parser.add_argument("--most-recent", action="store_true", help="Include summary and contents of recently changed/added files, copied to clipboard.")
    parser.add_argument("--llm", type=str, help="Specify the target LLM (e.g., 'Grok 3, built by xAI', 'LLaMA, built by Meta AI'); overrides last used LLM.")
    parser.add_argument("--use-static", action="store_true", help="Use static list of recent files from recent_files_fallback.json instead of dynamic scan.")
    parser.add_argument("--checkpoint", type=str, help="Save a checkpoint with the given message (implies --git unless --no-git is specified).")
    parser.add_argument("--no-git", action="store_true", help="Disable Git integration for checkpoint.")
    args = parser.parse_args()

    # Determine the target LLM: use --llm if provided, otherwise fall back to last used LLM
    if args.llm:
        target_llm = args.llm
        save_last_llm(target_llm)  # Update the last used LLM
    else:
        target_llm = get_last_llm()  # Use the last used LLM or default

    if args.checkpoint:
        result = run_checkpoint(args.checkpoint, use_git=not args.no_git)
        print(result)
    elif args.dump:
        dump_files()
    elif args.prompt:
        output = generate_prompt(most_recent=False, target_llm=target_llm, use_static=args.use_static)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
    elif args.most_recent:
        output = generate_prompt(most_recent=True, target_llm=target_llm, use_static=args.use_static)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt with recent files copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
    else:
        # Default behavior: same as --most-recent with last used or default LLM
        output = generate_prompt(most_recent=True, target_llm=target_llm, use_static=args.use_static)
        sys.stdout.write(output)
        sys.stdout.flush()
        if pyperclip:
            pyperclip.copy(output)
            print("Prompt with recent files copied to clipboard!", file=sys.stderr)
        else:
            print("Clipboard not available without pyperclip.", file=sys.stderr)
