# Grok-Local Usage Guide

This guide provides detailed instructions for using Grok-Local, a CLI agent for managing local Git repositories and files.

## Running the Agent
- **Interactive Mode**: `python grok_checkpoint.py`
  - Enter commands at the `Command:` prompt.
- **Non-Interactive Mode**: `python grok_checkpoint.py --ask "command"`
  - Executes a single command and exits.
- **Resume**: `python grok_checkpoint.py --resume`
  - Displays the last checkpoint.

## Supported Commands
### File Operations
- `create file <path>`: Creates a file at the specified path (e.g., `create file docs/new_file.txt`).
- `delete file <filename>`: Deletes a file from `safe/` (add `--force` to skip confirmation).
- `move file <src> to <dst>`: Moves a file (e.g., `move file local/temp.txt to docs/temp.txt`).
- `copy file <src> to <dst>`: Copies a file within `safe/`.
- `rename file <old> to <new>`: Renames a file in `safe/`.
- `read file <filename>`: Reads a file from `safe/`.
- `write <content> to <filename>`: Writes content to a file (defaults to `local/`).
- `list files`: Lists files in `safe/`.

### Git Operations
- `git status`: Shows repository status.
- `git pull`: Pulls latest changes.
- `git log [count]`: Displays commit history (default: 1).
- `git branch`: Lists branches.
- `git checkout <branch>`: Switches branches.
- `commit <message>`: Commits changes with a message.
- `git rm <filename>`: Removes a file from Git.
- `git diff`: Shows uncommitted changes.

### Checkpointing
- `checkpoint <description>`: Saves a project snapshot.
- `checkpoint <description> --file <filename>`: Saves to a custom file.
- `restore`: Restores `safe/` files from the last checkpoint.
- `restore --all`: Restores all tracked files.
- `restore --file <filename>`: Restores from a specific file.

### Delegation
- `create spaceship fuel script`: Delegates to Grok 3 for a fuel simulation script.
- `create x login stub`: Creates an X login stub via Grok 3.

## Examples
- Create and commit a doc: `create file docs/note.txt && write "Hello" to docs/note.txt && commit "Added note"`
- Move a file: `move file local/test.py to safe/test.py`
- Check Git status: `git status`

## Notes
- Commands can be chained with `&&` (e.g., `create file safe/test.txt && git status`).
- Set environment variables (e.g., `X_USERNAME`) for X-related tasks.
