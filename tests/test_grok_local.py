import os
import subprocess
import sys
import json

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

    print("All tests passed!")

if __name__ == "__main__":
    # Clean up any previous test files
    safe_dir = os.path.join(PROJECT_DIR, "safe")
    for file in ["test1.txt", "test2.txt"]:
        file_path = os.path.join(safe_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    test_sequence()
