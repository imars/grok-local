#!/usr/bin/env python3
import os
import subprocess
import logging
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_command(cmd, label, timeout=15):
    logger.info(f"Starting test: {label}")
    print(f"\n=== Testing {label} ===")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        print(stdout)
        if stderr:
            logger.error(f"Stderr for {label}: {stderr}")
            print(f"Stderr: {stderr}")
        logger.info(f"Test {label} completed: {stdout[:100]}...")
        return True, stdout, stderr
    except subprocess.TimeoutExpired as e:
        logger.error(f"Test {label} timed out after {timeout}s: {e}")
        print(f"Test timed out: {e.stdout}\nStderr: {e.stderr}")
        return False, e.stdout, e.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"Test {label} failed: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        print(f"Test failed: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        return False, e.stdout, e.stderr

def test_stub_mode():
    tests = [
        {
            "cmd": ["python", "x_poller.py", "--stub", "--debug", "--test"],
            "label": "x_poller.py stub mode (polling)",
            "expect": "Stubbed login successful"
        },
        {
            "cmd": ["python", "grok_local.py", "--stub", "--debug", "--ask", "create x login stub"],
            "label": "grok_local.py stub mode (delegation and Git)",
            "expect": "Created local/x_login_stub.py with X login stub and committed"
        },
        {
            "cmd": ["python", "grok_checkpoint.py", "--stub", "--ask", "checkpoint 'Stub Test' --git"],
            "label": "grok_checkpoint.py stub mode (checkpoint with Git)",
            "expect": "Checkpoint saved: 'Stub Test' --git to"
        },
        {
            "cmd": ["python", "grok_bootstrap.py", "--stub", "--prompt", "--debug"],
            "label": "grok_bootstrap.py stub mode (prompt with Git tree)",
            "expect": "Repository File Tree (stubbed):\n  .gitignore\n  grok_local.py\n  x_poller.py"
        }
    ]

    results = []
    for test in tests:
        passed, stdout, stderr = run_command(test["cmd"], test["label"])
        test_result = {
            "label": test["label"],
            "passed": passed and test["expect"] in stdout,
            "stdout": stdout,
            "stderr": stderr
        }
        results.append(test_result)

    print("\n=== Test Summary ===")
    for i, result in enumerate(results):
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {result['label']}")
        if not result["passed"]:
            print(f"  Expected: {tests[i]['expect']}\n  Got: {result['stdout'][:100]}...")
    logger.info(f"Completed stub mode test suite with {sum(r['passed'] for r in results)}/{len(results)} passing")

if __name__ == "__main__":
    os.chdir(PROJECT_DIR)
    test_stub_mode()
