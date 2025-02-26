import requests
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import logging
import subprocess
from logging.handlers import RotatingFileHandler
import argparse

PROJECT_DIR = os.getcwd()
GROK_URL = "https://x.com/i/grok?conversation=1894839609827512811"  # Hardcoded to this chat
COOKIE_FILE = os.path.join(PROJECT_DIR, "cookies.pkl")
CODE_BLOCK_DIR = os.path.join(PROJECT_DIR, "code_blocks")
DEBUG_DIR = os.path.join(PROJECT_DIR, "debug")

for directory in [CODE_BLOCK_DIR, DEBUG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[RotatingFileHandler("x_poller.log", maxBytes=1*1024*1024, backupCount=3)]
)

def handle_cookie_consent(driver, wait):
    try:
        consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]")))
        consent_button.click()
        logging.info("Clicked cookie consent button")
        time.sleep(2)
        return True
    except:
        logging.info("No cookie consent button found")
        return False

def cookies_valid(driver, url):
    driver.get(url)
    time.sleep(10)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        logging.info("Cookies validated successfully")
        return True
    except:
        logging.info("Cookie validation failed")
        return False

def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    logging.info(f"Saved {len(cookies)} cookies")

def load_cookies(driver):
    if not os.path.exists(COOKIE_FILE):
        logging.info("No cookie file found")
        return False
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.delete_all_cookies()
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logging.warning(f"Failed to add cookie: {e}")
    logging.info(f"Loaded {len(cookies)} cookies")
    return True

def perform_headless_login(driver, wait):
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    verify = os.getenv("X_VERIFY")
    
    if not all([username, password, verify]):
        logging.error("Missing credentials in environment variables")
        return False

    driver.get("https://x.com/login")
    logging.info("Navigating to login page")
    try:
        with open(os.path.join(DEBUG_DIR, "login_page.html"), "w") as f:
            f.write(driver.page_source)
        
        username_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        username_input.send_keys(username)
        logging.info("Entered username")
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Next')]")))
        next_button.click()
        time.sleep(3)

        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        password_input.send_keys(password)
        logging.info("Entered password")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Log in')]")))
        login_button.click()
        time.sleep(10)

        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_input.send_keys(verify)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            logging.info("Completed verification step")
            time.sleep(5)
        except:
            logging.info("No verification step required")

        if "login" not in driver.current_url.lower():
            save_cookies(driver)
            logging.info("Login successful")
            return True
        else:
            logging.error("Login failed, still on login page")
            with open(os.path.join(DEBUG_DIR, "login_failure.html"), "w") as f:
                f.write(driver.page_source)
            return False
    except Exception as e:
        logging.error(f"Login failed with exception: {e}")
        with open(os.path.join(DEBUG_DIR, "login_failure.html"), "w") as f:
            f.write(driver.page_source)
        return False

def scan_chat(driver, wait):
    driver.get(GROK_URL)
    time.sleep(10)
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(15):  # More scrolls to ensure bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    logging.info(f"Scanning chat at: {driver.current_url}")
    elements = driver.find_elements(By.TAG_NAME, "span")
    chat_content = [elem.get_attribute("textContent").strip() for elem in elements if elem.get_attribute("textContent").strip()]
    logging.info(f"Chat content (last 5): {' | '.join(chat_content[-5:])}... ({len(chat_content)} total lines)")
    return chat_content  # Return content directly

def ask_grok(prompt, fetch=False, headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(300)
    wait = WebDriverWait(driver, 180)

    try:
        driver.get("https://x.com")
        if load_cookies(driver) and cookies_valid(driver, GROK_URL):
            driver.get(GROK_URL)
            time.sleep(5)
        else:
            logging.info("Cookies invalid or not loaded, attempting login")
            if headless and not perform_headless_login(driver, wait):
                return "Headless login failed"
            driver.get(GROK_URL)
            time.sleep(5)
            handle_cookie_consent(driver, wait)

        return process_grok_interaction(driver, wait, prompt, fetch)
    except Exception as e:
        logging.error(f"ask_grok error: {e}")
        return f"Error: {e}"
    finally:
        driver.quit()

def process_grok_interaction(driver, wait, prompt, fetch):
    if fetch:
        chat_content = scan_chat(driver, wait)
        commands = []
        for text in chat_content:
            if "GROK_LOCAL:" in text.upper() and "GROK_LOCAL_RESULT:" not in text.upper():
                cmd = text.replace("GROK_LOCAL:", "").strip()
                valid_commands = ["what time is it?", "ask what time is it", "list files", "system info", "commit", "whoami", "scan chat"]
                if cmd.lower().startswith("commit ") or cmd.lower() in valid_commands:
                    commands.append(cmd)
                    logging.info(f"Found command: {cmd}")
        
        if not commands:
            logging.info("No GROK_LOCAL commands found")
            return "No GROK_LOCAL found after full scan"
        
        # Take the very last command
        last_command = commands[-1]
        logging.info(f"Selected last command: {last_command}")
        return last_command
    else:
        prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        prompt_box.clear()
        prompt_box.send_keys(prompt[:500])
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
        submit_button.click()
        time.sleep(10)
        return "Prompt submitted"

def poll_x(headless):
    logging.info("Starting polling loop")
    last_processed = None  # Track last command to avoid repeats
    while True:
        cmd = ask_grok("Polling for Grok 3...", fetch=True, headless=headless)
        if cmd and isinstance(cmd, str) and "Error" not in cmd and "found" not in cmd.lower():
            if cmd != last_processed:  # Only process if new
                print(f"Received: {cmd}")
                logging.info(f"Executing command: {cmd}")
                result = subprocess.run(
                    ["python", "grok_local.py", "--ask", cmd],
                    capture_output=True, text=True
                )
                output = result.stdout.strip() if result.stdout else f"Error: {result.stderr}"
                print(f"Result: {output}")
                logging.info(f"Command result: {output}")
                try:
                    ask_grok(f"GROK_LOCAL_RESULT: {output}", headless=headless)
                    logging.info(f"Posted result for {cmd}")
                    last_processed = cmd  # Update last processed
                except Exception as e:
                    logging.error(f"Failed to post result for {cmd}: {e}")
        else:
            print(f"Poll result: {cmd}")
            logging.info(f"Poll result: {cmd}")
        time.sleep(15)  # Faster loop

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll X for Grok 3 commands")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    poll_x(args.headless)
