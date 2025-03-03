# Grok-Local CLI Usage Guide

## Overview
Grok-Local is a command-line interface (CLI) tool for managing local files, Git repositories, and delegating tasks to Grok 3. It supports interactive mode, single commands via `--ask`, checkpointing for session state, and chat session restarting via `grok_bootstrap.py`.

## Scripts

### grok_local.py
The core CLI for file operations, Git commands, and Grok 3 delegation.

**Usage:**
- Interactive: `python grok_local.py`
- Single Command: `python grok_local.py --ask '<command>'`
- Debug Mode: `python grok_local.py --debug`

**Commands:**
- **File Operations:**
  - `create file <path>` - Create a file at <path>
  - `delete file <filename>` - Delete <filename> from safe/
  - `move file <src> to <dst>` - Move file from <src> to <dst>
  - `copy file <src> to <dst>` - Copy file from <src> to <dst>
  - `rename file <old> to <new>` - Rename file from <old> to <new>
  - `read file <filename>` - Read contents of <filename>
  - `write '<content>' to <filename>` - Write <content> to <filename>
  - `list files` - List files in safe/
- **Git Operations:**
  - `git status` - Show Git status
  - `git pull` - Pull changes from remote
  - `git log [count]` - Show last [count] commits (default 1)
  - `git branch` - List branches
  - `git checkout <branch>` - Switch to <branch>
  - `commit '<message>'` - Commit with <message> (use |<path> for specific file)
  - `git rm <filename>` - Remove <filename> from Git
  - `clean repo` - Remove untracked files
- **Checkpoint Operations:**
  - `list checkpoints` - List checkpoint files
  - `checkpoint '<description>' [--file <filename>] [with current x_poller.py content] [chat_url=<url>] [--git]` - Save a checkpoint
    - `--file <filename>`: Save to <filename> (default: checkpoint.json)
    - `with current x_poller.py content`: Include x_poller.py content
    - `chat_url=<url>`: Set exact chat URL (e.g., https://x.com/i/grok?conversation=123)
    - `--git`: Commit to Git
- **Utility:**
  - `what time is it` - Show UTC time
  - `version` - Show version (v0.1)
- **Delegation:**
  - `create spaceship fuel script` - Generate a fuel simulation script
  - `create x login stub` - Generate an X login stub

**Examples:**
- `python grok_local.py --ask 'checkpoint "Session backup" --file backup.json chat_url=https://x.com/i/grok?conversation=123 with current x_poller.py content'`
- `python grok_local.py --ask 'list files && git status'`

### grok_bootstrap.py
Restarts Grok 3 chat sessions with context from checkpoints and critical files.

**Usage:**
- `python grok_bootstrap.py [--debug] [--command '<cmd>'] [--dump] [--prompt] [--include-main]`

**Options:**
- `--debug`: Run grok_local.py with debug logs
- `--command '<cmd>'`: Run <cmd> via grok_local.py
- `--dump`: Dump critical file contents
- `--prompt`: Generate a restart prompt (includes chat URL and file content from checkpoint)
- `--include-main`: Include grok_local.py in prompt

**Examples:**
- `python grok_bootstrap.py --prompt` - Show latest checkpoint with chat URL
- `python grok_bootstrap.py --dump` - Dump all critical files

### grok_checkpoint.py
Manages checkpoint saving and listing.

**Usage:**
- `python grok_checkpoint.py [--resume] [--ask '<command>']`

**Commands:**
- `list checkpoints` - List checkpoint files
- `checkpoint '<desc>' [--file <filename>] [--task '<task>'] [--git] [chat_url=<url>]` - Save a checkpoint

**Examples:**
- `python grok_checkpoint.py --ask 'checkpoint "Backup" --file test.json chat_url=https://x.com/i/grok?conversation=123'`

## Notes
- Checkpoints save session state, including `chat_url` for exact chat resumption and `file_content` (e.g., x_poller.py).
- Use `grok_bootstrap.py --prompt` to restart a chat with the latest checkpoint details.
