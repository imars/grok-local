import os
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def mock_headless_login():
    logging.info("Mocking X login...")
    time.sleep(2)  # Simulate network delay
    username = os.getenv("X_USERNAME", "test_user")
    password = os.getenv("X_PASSWORD", "test_pass")
    verify = os.getenv("X_VERIFY", "test_verify")
    if username and password and verify:
        logging.info("Mock login successful")
        return True
    logging.error("Mock login failed: missing credentials")
    return False

def mock_poll_x():
    logging.info("Mock polling X...")
    time.sleep(1)
    return "GROK_LOCAL: list files"  # Dummy command

if __name__ == "__main__":
    if mock_headless_login():
        cmd = mock_poll_x()
        print(f"Mock command received: {cmd}")
    else:
        print("Mock login failed")
