# Grok-Local

A CLI tool for managing local files, Git repositories, and delegating tasks to Grok 3, with session checkpointing and restarting.

## Features
- File operations (create, delete, move, copy, rename, read, write, list).
- Git operations (status, pull, log, branch, checkout, commit, remove, clean).
- Checkpoint management (save/list with chat URLs and file content).
- Task delegation to Grok 3 (e.g., script generation).
- Session restarting via grok_bootstrap.py with detailed prompts.

## Setup
1. Clone: `git clone git@github.com:imars/grok-local.git`
2. Enter: `cd grok-local`
3. Env: `python -m venv venv && source venv/bin/activate && pip install gitpython`
4. Deps: `pip install -r requirements.txt`
5. Start: `python grok_local.py` or `python grok_bootstrap.py --prompt`

## Usage
See `docs/usage.md` for detailed command syntax and examples.

## Recent Updates (March 03, 2025)
- Added `chat_url` and `file_content` to checkpoints for precise session restoration.
- Enhanced --help outputs across all scripts.
