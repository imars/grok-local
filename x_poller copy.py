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

print("RUNNING VERSION 2025-02-26 PRECISE TIME MATCH")

PROJECT_DIR = os.getcwd()
GROK_URL = "https://x.com/i/grok?conversation=1894577188600676742"
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

def cookies_valid(driver):
    driver.get(GROK_URL)
    time.sleep(5)
    logging.info(f"Checking cookies - Title: {driver.title}")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        return True
    except:
        with open(os.path.join(DEBUG_DIR, "page_source_cookies.txt"), "w") as f:
            f.write(driver.page_source)
        logging.info("Cookie check failed - Page source saved to debug/page_source_cookies.txt")
        return False

def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    logging.info(f"Saved {len(cookies)} cookies to {COOKIE_FILE}")

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
            logging.warning(f"Failed to add cookie {cookie.get('name')}: {e}")
    logging.info(f"Loaded {len(cookies)} cookies")
    return True

def perform_headless_login(driver, wait):
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    verify = os.getenv("X_VERIFY")
    
    if not all([username, password, verify]):
        logging.error("Missing credentials in environment variables: X_USERNAME, X_PASSWORD, X_VERIFY")
        return False

    driver.get("https://x.com/login")
    logging.info("Navigating to login page")

    try:
        username_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        username_input.send_keys(username)
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Next')]")))
        next_button.click()
        time.sleep(2)

        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        password_input.send_keys(password)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Log in')]")))
        login_button.click()
        time.sleep(5)

        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_input.send_keys(verify)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            time.sleep(5)
        except:
            logging.info("No verification step required")

        if "login" not in driver.current_url.lower():
            save_cookies(driver)
            return True
        else:
            logging.error("Login failed, still on login page")
            return False
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False

def ask_grok(prompt, fetch=False, headless=False):
    logging.info(f"ask_grok called - prompt: {prompt}, fetch: {fetch}, headless: {headless}")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 60)

    driver.get("https://x.com")
    if load_cookies(driver):
        driver.get(GROK_URL)
        time.sleep(5)
        if cookies_valid(driver):
            logging.info("Cookies valid, proceeding with interaction")
            return process_grok_interaction(driver, wait, prompt, fetch)

    if headless:
        if not perform_headless_login(driver, wait):
            driver.quit()
            return "Headless login failed"
    else:
        driver.get("https://x.com/login")
        input("Log in with @ianatmars, then press Enter: ")
        handle_cookie_consent(driver, wait)
        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_value = input("Enter phone or email: ")
            verify_input.send_keys(verify_value)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            time.sleep(5)
        except:
            logging.info("No verification step required")
        save_cookies(driver)

    driver.get(GROK_URL)
    time.sleep(5)
    if handle_cookie_consent(driver, wait):
        time.sleep(2)

    return process_grok_interaction(driver, wait, prompt, fetch)

def process_grok_interaction(driver, wait, prompt, fetch):
    if fetch:
        logging.info(f"Scanning page at {driver.current_url}")
        elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']")
        logging.info(f"Total elements found: {len(elements)}")
        
        cmd_found = None
        for i, elem in enumerate(elements):
            text = elem.get_attribute("textContent").strip()
            if text.startswith("```") and text.endswith("```"):
                text = text[3:-3].strip()
            with open(os.path.join(CODE_BLOCK_DIR, f"code_block_{i}.txt"), "w") as f:
                f.write(text)
            logging.info(f"Saved code block to code_block_{i}.txt (raw: {text[:50]}...)")
            if "GROK_LOCAL:" in text and "GROK_LOCAL_RESULT:" not in text:
                cmd = text.replace("GROK_LOCAL:", "").strip()
                logging.info(f"Found GROK_LOCAL command in code_block_{i}.txt: {cmd}")
                # Exact match for "What time is it?" to avoid extra text
                if cmd == "What time is it?":
                    cmd_found = cmd
                    break
        
        if cmd_found:
            driver.quit()
            return cmd_found
        
        if len(elements) == 0:
            logging.info("No code blocks found, refreshing and checking all text")
            driver.refresh()
            time.sleep(5)
            elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']")
            logging.info(f"After refresh, total elements found: {len(elements)}")
            if len(elements) == 0:
                all_text = driver.find_elements(By.TAG_NAME, "div")
                for i, elem in enumerate(all_text):
                    text = elem.get_attribute("textContent").strip()
                    if text.startswith("```") and text.endswith("```"):
                        text = text[3:-3].strip()
                    with open(os.path.join(CODE_BLOCK_DIR, f"text_block_{i}.txt"), "w") as f:
                        f.write(text)
                    if "GROK_LOCAL:" in text and "GROK_LOCAL_RESULT:" not in text:
                        cmd = text.replace("GROK_LOCAL:", "").strip()
                        logging.info(f"Found GROK_LOCAL command in text_block_{i}.txt: {cmd}")
                        if cmd == "What time is it?":
                            cmd_found = cmd
                            break
                if cmd_found:
                    driver.quit()
                    return cmd_found
                with open(os.path.join(DEBUG_DIR, "page_source_full.txt"), "w") as f:
                    f.write(driver.page_source)
                logging.info("No GROK_LOCAL found - Page source saved to debug/page_source_full.txt")
        
        driver.quit()
        return "No GROK_LOCAL found after full scan"
    else:
        prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        prompt_box.clear()
        prompt_box.send_keys(prompt)
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
        submit_button.click()
        time.sleep(15)
        initial_count = len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']"))
        response_elements = wait.until(
            lambda driver: [
                elem.find_element(By.TAG_NAME, "pre")
                for elem in driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']")[initial_count:]
                if elem.get_attribute("textContent")
            ]
        )
        driver.quit()
        return response_elements[-1].get_attribute("textContent")

def poll_x(headless):
    while True:
        cmd = ask_grok("Polling for Grok 3...", fetch=True, headless=headless)
        if cmd and "Cookie" not in cmd and "Failed" not in cmd:
            print(f"Received: {cmd}")
            if cmd.startswith("ask "):
                result = subprocess.run(
                    ["python", "grok_local.py", "--ask", cmd[4:]],
                    capture_output=True, text=True
                )
                print(f"Result: {result.stdout if result.stdout else 'Error: ' + result.stderr}")
                ask_grok(f"GROK_LOCAL_RESULT: {result.stdout}", headless=headless)
            elif cmd == "No GROK_LOCAL found after full scan":
                print("No command found, continuing to poll")
            else:
                result = subprocess.run(
                    ["python", "grok_local.py", "--ask", cmd],
                    capture_output=True, text=True
                )
                print(f"Result: {result.stdout if result.stdout else 'Error: ' + result.stderr}")
                ask_grok(f"GROK_LOCAL_RESULT: {result.stdout}", headless=headless)
        else:
            print(f"Poll failed: {cmd}")
        time.sleep(30)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Poll X for Grok 3 commands")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    poll_x(args.headless)
