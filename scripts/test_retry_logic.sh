#!/bin/bash
# Test script for retry logic in git_ops.py's git_commit_and_push function

# Ensure venv is active (optional if already active)
source ../venv/bin/activate

# Create a test file to commit
echo "Test retry logic" > test_file.txt

# Commit and push with retry logic
python ../grok_local.py --ask "commit 'Test retry logic commit'"

# Simulate a network failure by committing again (manual interruption optional)
echo "Simulating push with potential retry..."
python ../grok_local.py --ask "commit 'Test retry logic again'"

# Check logs for retry attempts
echo "Checking grok_local.log for retry attempts..."
grep "Push attempt" ../grok_local.log

# Cleanup
rm test_file.txt

echo "Test complete. Check GitHub for commits: https://github.com/imars/grok-local"
