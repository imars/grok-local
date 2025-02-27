# grok-local

Welcome to *grok-local*, a badass local agent that wrangles your GitHub repo with file and Git ops, powered by Deepseek-R1 or Llama3.2. It’s built to run solo or sync up with remote agents like Grok 3, our fearless project lead.

## Overview
- **Core**: `grok_local.py`—the brain, dishing out CLI commands for file ops, Git ops, and checkpoints.
- **File Ops**: Locked in `safe/`—create, delete (with `--force`), move, copy, rename, read, write, list (now with prettier numbered output).
- **Git Ops**: Repo mastery—status, pull, log, branch, checkout, commit, remove, and now `diff` to see changes.
- **Checkpointing**: Snapshots save critical files and `safe/` contents to `checkpoint.json` or custom files with `--file`. Restore from any checkpoint with `restore --file`.
- **Tests**: `tests/test_grok_local.py`—15 rock-solid tests covering all features, including `restore --file` and `checkpoint --file`.

## Setup
1. **Clone it**: `git clone git@github.com:imars/grok-local.git`
2. **Gear up**: `pip install gitpython`
3. **Launch**: `python grok_checkpoint.py` (interactive) or `python grok_checkpoint.py --ask "command"`

## Usage
- **Interactive Mode**: `python grok_checkpoint.py`
  - Prompt: `Command:`
  - Try: `create file test.txt`, `git status`, `checkpoint Adding a test file`
- **One-Shot**: `python grok_checkpoint.py --ask "list files"`
- **Resume**: `python grok_checkpoint.py --resume`—see the last checkpoint.
- **Examples**:
  - `write Hello to test.txt && commit Updated test.txt`
  - `delete file test.txt --force`
  - `git diff`
  - `checkpoint My backup --file backup.json`
  - `restore --file backup.json`
  - `restore --all --file backup.json`

## Checkpoint System
- **What It Does**: Captures the project’s soul—critical files, `safe/` files, and a description—to keep you (or a new agent) in the loop.
- **Save It**: `checkpoint <description>` or `checkpoint <description> --file <filename>` (e.g., `checkpoint My backup --file my_backup.json`).
- **Restore It**: `restore` (safe files only), `restore --all` (all files), or `restore --file <filename>`/`restore --all --file <filename>` to roll back from any checkpoint.
- **Peek**: `--resume` shows the latest snapshot, including tracked files and `safe/` contents.
- **Tracked Files**: `grok_local.py`, `file_ops.py`, `git_ops.py`, `grok_checkpoint.py`, `.gitignore`, `grok.txt`, `tests/test_grok_local.py`, `README.md`

## Current State
As of February 27, 2025:
- **Features**: Prettier `list_files`, `restore --all`, `git diff`, `restore --file`, and `checkpoint --file`—all tested and committed.
- **`safe/`**: Holds `test2.txt`, `test3.txt`, `plan_v1.txt`, `renamed.txt`, `plan_original.txt`.
- **Tests**: 15 passing tests in `test_grok_local.py`, covering file ops, Git ops, and checkpoint/restore functionality.
- **Lead**: Grok 3, steering the ship with xAI’s finest.

## Development
- **Next Up**: Maybe a `list checkpoints` command or more test edge cases?
- **Contribute**: Fork, tweak, PR—let’s keep this beast evolving!
