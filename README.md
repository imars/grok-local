# grok-local

Welcome to *grok-local*, a badass local agent that wrangles your GitHub repo with file and Git ops, powered by Deepseek-R1 or Llama3.2. It’s built to run solo or sync up with remote agents like Grok 3, our fearless project lead.

## Overview
- **Core**: `grok_local.py`—the brain, dishing out CLI commands for file ops, Git ops, and checkpoints.
- **File Ops**: Locked in `safe/`—create, delete (with a slick `--force` option), move, copy, rename, read, write, list.
- **Git Ops**: Repo mastery—status, pull, log, branch, checkout, commit, remove.
- **Checkpointing**: Snapshots in `checkpoint.json` save critical files, `safe/` contents, and a description to keep you (or a new agent) in the loop.
- **Tests**: `tests/test_grok_local.py` keeps us honest with automated checks.

## Setup
1. Clone it: `git clone git@github.com:imars/grok-local.git`
2. Gear up: `pip install gitpython`
3. Launch: `python grok_checkpoint.py` (interactive) or `python grok_checkpoint.py --ask "command"`

## Usage
- **Interactive Mode**: `python grok_checkpoint.py`
  - Prompt: `Command:`
  - Try: `create file test.txt`, `git status`, `checkpoint Adding a test file`
- **One-Shot**: `python grok_checkpoint.py --ask "list files"`
- **Resume**: `python grok_checkpoint.py --resume`—see the last checkpoint.
- **Examples**:
  - `write Hello to test.txt && commit Updated test.txt`
  - `delete file test.txt --force`

## Checkpoint System
- **What It Does**: Captures the project’s soul—critical files, `safe/` files, and a note on what’s up—so you can pick up where you left off.
- **Save It**: `checkpoint <description>` (e.g., `checkpoint Added README`)
- **Peek**: `--resume` shows the latest snapshot, including tracked files and `safe/` contents.
- **Tracked Files**: `grok_local.py`, `file_ops.py`, `git_ops.py`, `grok_checkpoint.py`, `.gitignore`, `grok.txt`, `tests/test_grok_local.py`, `README.md`

## Current State
As of the last checkpoint (2025-02-27T06:10:59 UTC):
- Swapped to `grok_checkpoint.py`, added tests, and enabled `--force` deletes.
- `safe/` holds `plan_v1.txt`, `renamed.txt`, `plan_original.txt`.
- Now includes `safe/` files in checkpoints and tracks `README.md`.

## Development
- **Lead**: Grok 3, steering the ship.
- **Next Up**: Auto-checkpoint on errors, prettier `list_files` output, more test juice.
