import requests
import git
import os
import pickle
import argparse
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from git.exc import GitCommandError
import logging

# Config
PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
GROK_URL = "https://x.com/i/grok?conversation=1894190038096736744"
COOKIE_FILE = os.path.join(PROJECT_DIR, "cookies.pkl")

# Setup logging
logging.basicConfig(filename="agent.log", level=logging.DEBUG, format="%(asctime)s - %(message)s")

def git_push(message="Automated commit"):
    logging.debug(f"Starting git_push with message: {message}")
    repo = git.Repo(PROJECT_DIR)
    repo.git.add(A=True)
    logging.debug("Files staged")
    try:
        repo.git.commit(m=message)
        logging.debug("Commit made")
    except GitCommandError as e:
        if "nothing to commit" in str(e):
            logging.debug("No changes to commit - proceeding")
        else:
            raise
    repo.git.push()
    logging.debug("Push completed")
    return "Pushed to GitHub or already up-to-date"

def read_file(filename):
    logging.debug(f"Reading file: {filename}")
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        content = f.read()
    logging.debug(f"File read: {content}")
    return content

def get_multiline_input(prompt):
    print(prompt)
    print("Paste response below, then press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows):")
    response = sys.stdin.read()
    return response.strip()

def cookies_valid(driver):
    driver.get(GROK_URL)
    time.sleep(2)
    logging.debug(f"Page title after cookie load: {driver.title}")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        return "Grok" in driver.title
    except:
        return False

def ask_grok(prompt, headless=False):
    logging.debug(f"Starting ask_grok with prompt: {prompt}, headless={headless}")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        logging.debug("Initializing ChromeDriver (headless)")
    else:
        logging.debug("Initializing ChromeDriver (GUI mode)")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 180)

    logging.debug(f"Navigating to {GROK_URL}")
    driver.get(GROK_URL)

    if os.path.exists(COOKIE_FILE) and headless:
        logging.debug("Loading cookies")
        try:
            cookies = pickle.load(open(COOKIE_FILE, "rb"))
            driver.delete_all_cookies()
            for cookie in cookies:
                driver.add_cookie(cookie)
            logging.debug("All cookies loaded")
            driver.refresh()
            time.sleep(2)
            if not cookies_valid(driver):
                logging.debug("Cookies invalid or rejected")
                driver.quit()
                return "Cookies invalid - run without --headless to re-login"
        except Exception as e:
            logging.debug(f"Cookie loading failed: {e}")
            driver.quit()
            return "Cookie file corrupted - run without --headless to regenerate"
    else:
        logging.debug("No cookies or GUI mode - forcing manual login")
        driver.get("https://x.com/login")
        logging.debug("At login page, waiting for user input")
        input("Log in with @ianatmars, then press Enter: ")
        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_value = input("Enter phone (e.g., +1...) or email for verification: ")
            verify_input.send_keys(verify_value)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            logging.debug("Verification submitted")
            time.sleep(5)
        except:
            logging.debug("No verification prompt detected")
        driver.get(GROK_URL)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
    pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))
    logging.debug("Cookies saved")

    try:
        prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        logging.debug("Sending prompt to input")
        prompt_box.clear()
        prompt_box.send_keys(prompt)
        time.sleep(1)
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
        submit_button.click()
        logging.debug("Prompt submitted")
        time.sleep(5)  # Wait for reply to start

        logging.debug("Waiting for response")
        initial_count = len(driver.find_elements(By.CLASS_NAME, "css-146c3p1"))
        logging.debug(f"Initial response count: {initial_count}")
        response_elements = wait.until(
            lambda driver: [
                elem for elem in driver.find_elements(By.CLASS_NAME, "css-146c3p1")[initial_count:]
                if elem.get_attribute("textContent").strip() and 
                   "Grok" in elem.get_attribute("textContent") and 
                   "```python" in elem.get_attribute("textContent").lower() and  # Look for code block
                   all(p not in elem.get_attribute("textContent").lower() for p in ["optimize this code", "def greet(name):"]) and
                   any(r in elem.get_attribute("textContent").lower() for r in ["here’s", "optimized", "version"])
            ],
            message="No new Grok response with code appeared"
        )
        full_response = response_elements[-1].get_attribute("textContent")
        logging.debug(f"Response received: {full_response}")
        pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))
        return full_response
    except Exception as e:
        logging.debug(f"Error occurred: {e}")
        with open("page_source.html", "w") as f:
            f.write(driver.page_source)
        logging.debug("Full page source saved to page_source.html")
        print(f"Manual fallback - paste this to Grok:\n{prompt}")
        response = get_multiline_input("Enter Grok's response here:")
        logging.debug(f"Grok replied: {response}")
        return response
    finally:
        logging.debug("Closing browser")
        driver.quit()

def local_reasoning(task):
    logging.debug(f"Starting local_reasoning with task: {task}")
    try:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": f"Briefly summarize steps to {task}"}]
        }
        logging.debug(f"Sending request to {OLLAMA_URL}/api/chat")
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        full_response = ""
        logging.debug("Receiving streamed response")
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                if "message" in chunk and "content" in chunk["message"]:
                    full_response += chunk["message"]["content"]
                    logging.debug(f"Chunk received after {time.time() - start_time:.2f}s: {chunk['message']['content']}")
                if chunk.get("done", False):
                    logging.debug(f"Stream completed after {time.time() - start_time:.2f}s")
                    break
        logging.debug(f"Local reasoning result: {full_response}")
        return full_response
    except requests.exceptions.RequestException as e:
        result = f"Ollama error: {e}"
        logging.debug(f"Local reasoning failed: {result}")
        return result

def main():
    parser = argparse.ArgumentParser(description="Run the agent with optional headless mode")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    args = parser.parse_args()

    logging.debug("Starting main")
    task = "push main.py to GitHub"
    plan = local_reasoning(task)
    print(f"Plan: {plan}")

    code = read_file("main.py")
    git_result = git_push(f"Update main.py: {time.ctime()}")
    print(f"Git result: {git_result}")

    prompt = f"Optimize this code:\n{code}"
    grok_response = ask_grok(prompt, headless=args.headless)
    print(f"Grok says:\n{grok_response}")

if __name__ == "__main__":
    main()
