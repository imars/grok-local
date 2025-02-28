# Grok-Local

Grok-Local is a command-line interface (CLI) agent designed to manage local GitHub repositories with advanced file and Git operations. Built with Deepseek-R1 or Llama3.2, it operates independently or integrates with remote agents like Grok 3, the designated project lead. This tool supports a wide range of development tasks, from file management to version control and checkpointing, with a focus on flexibility and automation.

## Overview
- **Core**: `grok_local.py`—the primary script providing CLI commands for file operations, Git management, and state checkpointing.
- **File Operations**: Supports creating, deleting (with `--force`), moving, copying, renaming, reading, writing, and listing files across any directory (e.g., `safe/`, `local/`, `docs/`), with improved path handling.
- **Git Operations**: Comprehensive repository management—status, pull, log, branch, checkout, commit, remove, and diff—ensuring robust version control.
- **Checkpointing**: Captures project states (critical files and `safe/` contents) in `checkpoint.json` or custom files via `--file`. Restore with `restore --file` or `--all`.
- **Tests**: `tests/test_grok_local.py`—15+ unit tests validating file ops, Git ops, and checkpoint/restore functionality.

## Setup
1. **Clone the Repository**: `git clone git@github.com:imars/grok-local.git`
2. **Install Dependencies**: `pip install gitpython` (additional requirements in `requirements.txt` if present).
3. **Run the Agent**: 
   - Interactive: `python grok_checkpoint.py`
   - Non-Interactive: `python grok_checkpoint.py --ask "command"`

## Usage
- **Interactive Mode**: Launch with `python grok_checkpoint.py` and enter commands at the `Command:` prompt.
  - Example: `create file docs/new_file.txt`, `git status`, `checkpoint Project snapshot`
- **Non-Interactive Mode**: Execute a single command with `python grok_checkpoint.py --ask "list files"`.
- **Resume**: View the last checkpoint with `python grok_checkpoint.py --resume`.
- **Command Examples**:
  - `write "Project notes" to docs/notes.txt && commit "Added notes"`
  - `delete file safe/test.txt --force`
  - `git diff`
  - `checkpoint "Backup state" --file backup.json`
  - `restore --file backup.json`
  - `restore --all --file backup.json`

## Checkpoint System
- **Purpose**: Preserves project state—critical files, `safe/` contents, and descriptions—for continuity across sessions or agent handoffs.
- **Save**: `checkpoint "description"` or `checkpoint "description" --file <filename>` (e.g., `checkpoint "My backup" --file my_backup.json`).
- **Restore**: `restore` (safe files only), `restore --all` (all files), or `restore --file <filename>`/`restore --all --file <filename>`.
- **View**: `--resume` displays the latest checkpoint, including tracked files and `safe/` contents.
- **Tracked Files**: `grok_local.py`, `file_ops.py`, `git_ops.py`, `grok_checkpoint.py`, `.gitignore`, `grok.txt`, `tests/test_grok_local.py`, `README.md`

## Current State (February 28, 2025)
- **Features**: Enhanced file operations with arbitrary path support, `git diff`, `restore --all`, and custom checkpoint files. Added `local/x_login_stub.py` for X login simulation and `docs/timeline.md` for project documentation.
- **Directories**:
  - `safe/`: Sandboxed files (`test2.txt`, `test3.txt`, `plan_v1.txt`, `renamed.txt`, `plan_original.txt`).
  - `local/`: Working files (`spaceship_fuel.py`, `x_login_stub.py`).
  - `docs/`: Documentation (`timeline.md`, `.placeholder`).
- **Tests**: 15+ passing tests in `test_grok_local.py`, covering core functionality.
- **Lead**: Grok 3, guiding development with xAI’s expertise.

## Development
- **Next Steps**:
  - Integrate `x_login_stub.py` into `x_poller.py` for safe X polling.
  - Add a `list checkpoints` command for better checkpoint management.
  - Enhance `git_commit_and_push` for reliability.
- **Contributing**: Fork the repository, implement changes, and submit a pull request to contribute to Grok-Local’s evolution.

For detailed goals and milestones, see `docs/timeline.md`.
