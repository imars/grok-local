import subprocess
import os
import json
import sys
import time
import tempfile
from pathlib import Path

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
PORT = 9222
CHAT_FILE = Path("x_chats.json")
BRAVE_FACE_SCRIPT = Path("brave_face.js")
GROK_LOCAL_TEST_CHANNEL = "https://x.com/i/grok?conversation=1895083745784254635"

X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")
X_VERIFY = os.getenv("X_VERIFY")

def ensure_brave_running():
    result = subprocess.run(["lsof", f"-i:{PORT}"], capture_output=True, text=True)
    if "Brave" not in result.stdout:
        print("Launching Brave with debugging port...")
        temp_dir = tempfile.mkdtemp(prefix="brave_session_")
        try:
            process = subprocess.Popen(
                [BRAVE_PATH, f"--remote-debugging-port={PORT}", f"--user-data-dir={temp_dir}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            print(f"Brave process started with PID: {process.pid}")
            for attempt in range(10):
                time.sleep(2)
                print(f"Checking port 9222 (attempt {attempt + 1}/10)...")
                result = subprocess.run(["lsof", f"-i:{PORT}"], capture_output=True, text=True)
                if "Brave" in result.stdout:
                    print("✓ Brave is running on port 9222.")
                    return
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print(f"✗ Brave process exited early. Exit code: {process.returncode}")
                    print(f"Brave stdout: {stdout}")
                    print(f"Brave stderr: {stderr}")
                    exit(1)
            print("✗ Failed to confirm Brave started on port 9222 after 20 seconds.")
            stdout, stderr = process.communicate()
            print(f"Brave stdout: {stdout}")
            print(f"Brave stderr: {stderr}")
            exit(1)
        except Exception as e:
            print(f"✗ Failed to launch Brave: {e}")
            exit(1)
    else:
        print("Brave already running on port 9222.")

def run_brave_face(close_browser=False, action="connect"):
    if not BRAVE_FACE_SCRIPT.exists():
        print(f"Error: {BRAVE_FACE_SCRIPT} not found in {os.getcwd()}!")
        exit(1)
    
    cmd = ["node", str(BRAVE_FACE_SCRIPT), f"--action={action}"]
    if close_browser:
        cmd.append("--test")
    if X_USERNAME:
        cmd.extend(["--username", X_USERNAME])
    if X_PASSWORD:
        cmd.extend(["--password", X_PASSWORD])
    if X_VERIFY:
        cmd.extend(["--verify", X_VERIFY])
    
    log_cmd = ["node", str(BRAVE_FACE_SCRIPT), f"--action={action}"]
    if close_browser:
        log_cmd.append("--test")
    if X_USERNAME:
        log_cmd.extend(["--username", X_USERNAME])
    if X_PASSWORD:
        log_cmd.extend(["--password", "[REDACTED]"])
    if X_VERIFY:
        log_cmd.extend(["--verify", "[REDACTED]"])
    
    print(f"Running Brave interface: {' '.join(log_cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error running brave_face.js: {result.stderr}")
        exit(1)
    return result.stdout

def save_chat_tabs(chat_urls):
    chat_urls = [GROK_LOCAL_TEST_CHANNEL]
    with CHAT_FILE.open("w") as f:
        json.dump(chat_urls, f, indent=2)
    print(f"Saved {len(chat_urls)} chat tabs to {CHAT_FILE}")

def restore_chat_tabs(current_tabs):
    chat_urls = [GROK_LOCAL_TEST_CHANNEL]
    print(f"Restoring test channel if not present...")
    if GROK_LOCAL_TEST_CHANNEL not in current_tabs:
        run_brave_face(action=f"open-tab={GROK_LOCAL_TEST_CHANNEL}")
        print(f" - Restored {GROK_LOCAL_TEST_CHANNEL}")
    else:
        print(f" - Test channel {GROK_LOCAL_TEST_CHANNEL} already open.")

def test_communication():
    # Skip reading for now, send a test message
    print("Sending test message from grok_local...")
    run_brave_face(action=f"send-message=Hello from grok_local at {time.strftime('%H:%M:%S')}")

def main():
    close_browser = "--test" in sys.argv
    
    print("Starting X Chat Manager Script")
    print("==============================")
    print(f"Close browser after run: {close_browser}")
    if X_USERNAME and X_PASSWORD and X_VERIFY:
        print("Using credentials from environment variables (username, password, verify).")
    else:
        print("Warning: One or more of X_USERNAME, X_PASSWORD, X_VERIFY not set in env vars.")

    ensure_brave_running()
    output = run_brave_face(close_browser=close_browser, action="connect")
    
    if "Successfully loaded X messages" in output or "Already logged in to X" in output:
        current_tabs = [line.split("URL: ")[1] for line in output.splitlines() if "URL: " in line]
        if current_tabs:
            save_chat_tabs(current_tabs)
        restore_chat_tabs(current_tabs)
        test_communication()
    
    print("==============================")
    print("Script finished")

if __name__ == "__main__":
    main()