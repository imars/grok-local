import os
import subprocess
import sys
import json
import shutil

# Ensure we're in the project root
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_DIR)
sys.path.append(PROJECT_DIR)

from grok_local import ask_local

def run_command(cmd, use_subprocess=False):
    """Run a command either via ask_local or subprocess."""
    if use_subprocess:
        result = subprocess.run(
            ["python", "grok_local.py", "--ask", cmd],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    else:
        return ask_local(cmd)

def test_sequence():
    print("Starting test sequence...")
    safe_dir = os.path.join(PROJECT_DIR, "safe")

    # Clean slate
    if os.path.exists(safe_dir):
        shutil.rmtree(safe_dir)

    # Test 1: Create a file
    result = run_command("create file test1.txt")
    print(f"Create file: {result}")
    assert "Created file: test1.txt" in result, "File creation failed"

    # Test 2: Write to the file
    result = run_command("write Hello, Grok! to test1.txt")
    print(f"Write to file: {result}")
    assert "Wrote to test1.txt: Hello, Grok!" in result, "File write failed"

    # Test 3: Read the file
    result = run_command("read file test1.txt")
    print(f"Read file: {result}")
    assert "Content of test1.txt: Hello, Grok!" in result, "File read failed"

    # Test 4: Delete with force
    result = run_command("delete file test1.txt --force")
    print(f"Delete with force: {result}")
    assert "Deleted file: test1.txt" in result, "Forced delete failed"

    # Test 5: Git status
    result = run_command("git status")
    print(f"Git status: {result}")
    assert "On branch" in result, "Git status failed"

    # Test 6: Multi-command
    result = run_command("create file test2.txt && write Test2 to test2.txt")
    print(f"Multi-command: {result}")
    assert "Created file: test2.txt" in result and "Wrote to test2.txt: Test2" in result, "Multi-command failed"

    # Test 7: Checkpoint
    result = run_command("checkpoint Test checkpoint with test2.txt")
    print(f"Checkpoint: {result}")
    assert "Checkpoint saved: Test checkpoint with test2.txt" in result, "Checkpoint failed"
    with open(os.path.join(PROJECT_DIR, "checkpoint.json"), "r") as f:
        checkpoint = json.load(f)
    assert checkpoint["description"] == "Test checkpoint with test2.txt", "Checkpoint description mismatch"
    assert "grok_local.py" in checkpoint["files"], "Checkpoint missing critical files"
    assert "test2.txt" in checkpoint["safe_files"], "Checkpoint missing safe files"

    # Test 8: Empty safe directory
    shutil.rmtree(safe_dir)  # Clear safe/
    result = run_command("list files")
    print(f"List empty safe/: {result}")
    assert "No files in safe directory" in result, "Empty safe/ list failed"

    # Test 9: Invalid file name
    result = run_command("create file grok_local.py")
    print(f"Invalid file name: {result}")
    assert "Error: Invalid or protected filename" in result, "Invalid file name check failed"

    # Test 10: Auto-checkpoint on Git error (simulate no remote)
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    result = run_command("git pull", use_subprocess=True)
    print(f"Git pull error: '{result}'")
    assert "git pull error" in result.lower(), "Git pull error not triggered"
    with open(os.path.join(PROJECT_DIR, "checkpoint.json"), "r") as f:
        checkpoint = json.load(f)
    assert "git pull failed" in checkpoint["description"].lower(), "Auto-checkpoint on Git error failed"

    # Restore remote
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:imars/grok-local.git"], capture_output=True)

    # Test 11: Prettier list_files
    run_command("create file test2.txt")  # Recreate test2.txt
    run_command("create file test3.txt")
    result = run_command("list files")
    print(f"Pretty list files: {result}")
    assert "1. test2.txt" in result and "2. test3.txt" in result, "Pretty list_files failed"

    print("All tests passed!")

if __name__ == "__main__":
    test_sequence()
