import requests
import git
import os
import pickle
import argparse
import sys
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from git.exc import GitCommandError
import logging
import re

# Config
PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
GROK_URL = "https://x.com/i/grok?conversation=1894190038096736744"
COOKIE_FILE = os.path.join(PROJECT_DIR, "cookies.pkl")
SAFE_COMMANDS = {"grep", "tail", "cat", "ls", "dir", "head"}

# Setup logging
logging.basicConfig(filename="agent.log", level=logging.DEBUG, format="%(asctime)s - %(message)s")

def git_push(message="Automated commit"):
    repo = git.Repo(PROJECT_DIR)
    repo.git.add(A=True)
    try:
        repo.git.commit(m=message)
    except GitCommandError as e:
        if "nothing to commit" in str(e):
            pass
        else:
            raise
    repo.git.push()
    return "Pushed to GitHub or already up-to-date"

def read_file(filename):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        return f.read()

def write_file(filename, content):
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)

def get_multiline_input(prompt):
    print(prompt)
    print("Paste response below, then press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows):")
    return sys.stdin.read().strip()

def run_command(command_str):
    parts = command_str.split()
    if not parts or parts[0].lower() not in SAFE_COMMANDS:
        return f"Error: Only {', '.join(SAFE_COMMANDS)} allowed"
    if any(danger in command_str.lower() for danger in ["sudo", "rm", "del", ";", "&", "|"]):
        return "Error: Unsafe command"
    args = [arg if not arg.startswith('/') else os.path.join(PROJECT_DIR, arg[1:]) for arg in parts[1:]]
    full_cmd = [parts[0]] + args
    try:
        result = subprocess.run(full_cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def ask_local(request):
    if any(cmd in request.lower() for cmd in SAFE_COMMANDS):
        return run_command(request)
    return local_reasoning(request)

def cookies_valid(driver):
    driver.get(GROK_URL)
    time.sleep(2)
    logging.debug(f"Checking cookies - Title: {driver.title}")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        return "Grok" in driver.title
    except:
        return False

def ask_grok(prompt, headless=False, fetch=False):
    logging.debug(f"ask_grok called - prompt: {prompt}, headless: {headless}, fetch: {fetch}")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 60)  # Shortened for debugging

    logging.debug(f"Navigating to {GROK_URL}")
    driver.get(GROK_URL)
    if os.path.exists(COOKIE_FILE) and headless:
        try:
            cookies = pickle.load(open(COOKIE_FILE, "rb"))
            driver.delete_all_cookies()
            for cookie in cookies:
                driver.add_cookie(cookie)
            logging.debug("Cookies loaded, refreshing")
            driver.refresh()
            time.sleep(5)
            if not cookies_valid(driver):
                logging.debug("Cookies invalid")
                driver.quit()
                return "Cookies invalid"
        except Exception as e:
            logging.debug(f"Cookie loading failed: {e}")
            driver.quit()
            return "Cookie error"
    else:
        driver.get("https://x.com/login")
        input("Log in with @ianatmars, then press Enter: ")
        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_value = input("Enter phone or email: ")
            verify_input.send_keys(verify_value)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            time.sleep(5)
        except:
            pass
        driver.get(GROK_URL)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
    pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))

    try:
        if fetch:
            logging.debug("Fetching command from X")
            initial_count = len(driver.find_elements(By.CLASS_NAME, "css-146c3p1"))
            logging.debug(f"Initial element count: {initial_count}")
            response_elements = wait.until(
                lambda driver: [
                    elem for elem in driver.find_elements(By.CLASS_NAME, "css-146c3p1")[initial_count:]
                    if elem.get_attribute("textContent").startswith("GROK_LOCAL:")
                ],
                message="No GROK_LOCAL command found"
            )
            cmd = response_elements[-1].get_attribute("textContent").replace("GROK_LOCAL:", "").strip()
            logging.debug(f"Command fetched: {cmd}")
            return cmd
        else:
            logging.debug("Sending prompt to X")
            prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
            prompt_box.clear()
            prompt_box.send_keys(prompt)
            submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
            submit_button.click()
            time.sleep(15)  # Shortened for debugging
            initial_count = len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']"))
            logging.debug(f"Initial markdown count: {initial_count}")
            response_elements = wait.until(
                lambda driver: [
                    elem.find_element(By.TAG_NAME, "pre")
                    for elem in driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown-code-block']")[initial_count:]
                    if "optimized" in elem.get_attribute("textContent").lower()
                ]
            )
            response = response_elements[-1].get_attribute("textContent")
            logging.debug(f"Response received: {response}")
            return response
    except Exception as e:
        logging.debug(f"Error in ask_grok: {e}")
        with open("page_source.html", "w") as f:
            f.write(driver.page_source)
        return f"Failed: {e}"
    finally:
        logging.debug("Closing driver")
        driver.quit()

def local_reasoning(task):
    try:
        payload = {"model": MODEL, "messages": [{"role": "user", "content": task}]}
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120)
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                if "message" in chunk and "content" in chunk["message"]:
                    full_response += chunk["message"]["content"]
                if chunk.get("done", False):
                    break
        return full_response
    except requests.exceptions.RequestException as e:
        return f"Ollama error: {e}"

def command_prompt():
    print("Commands: optimize <file>, push <message>, run <cmd>, ask <request>, poll, exit")
    while True:
        cmd = input("> ").strip().split(maxsplit=1)
        if not cmd:
            continue
        action = cmd[0].lower()

        if action == "exit":
            print("Goodbye!")
            break
        elif action == "optimize" and len(cmd) > 1:
            filename = cmd[1]
            if not os.path.exists(os.path.join(PROJECT_DIR, filename)):
                print(f"File {filename} not found")
                continue
            code = read_file(filename)
            prompt = f"Optimize this code:\n{code}"
            response = ask_grok(prompt, headless=True)
            if response and "Cookie" not in response and "Failed" not in response:
                print(f"Optimized via X:\n{response}")
                if "```python" in response:
                    code = response.split('```python\n')[1].split('```')[0].strip()
                    write_file(filename, code)
                    print(f"Updated {filename}")
            else:
                response = local_reasoning(prompt)
                print(f"Optimized locally:\n{response}")
                if "```python" in response:
                    code = response.split('```python\n')[1].split('```')[0].strip()
                    write_file(filename, code)
                    print(f"Updated {filename}")
        elif action == "push" and len(cmd) > 1:
            print(git_push(cmd[1]))
        elif action == "run" and len(cmd) > 1:
            print(run_command(cmd[1]))
        elif action == "ask" and len(cmd) > 1:
            print(f"Local response:\n{ask_local(cmd[1])}")
        elif action == "poll":
            print("Polling X for Grok 3 commands...")
            cmd = ask_grok("Waiting for Grok 3...", headless=True, fetch=True)
            if cmd and "Cookie" not in cmd and "Failed" not in cmd:
                print(f"Received: {cmd}")
                if cmd.startswith("ask "):
                    result = ask_local(cmd[4:])
                    print(f"Result:\n{result}")
                    ask_grok(f"GROK_LOCAL_RESULT: {result}", headless=True)
                else:
                    print("Unknown command format")
            else:
                print(f"Poll failed: {cmd or 'No response'}")
        else:
            print("Unknown command. Try: optimize <file>, push <message>, run <cmd>, ask <request>, poll, exit")

def main():
    parser = argparse.ArgumentParser(description="Run the agent with optional modes")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--prompt", action="store_true")
    args = parser.parse_args()

    if args.prompt:
        command_prompt()
    else:
        task = "push main.py to GitHub"
        plan = local_reasoning(f"Briefly summarize steps to {task}")
        print(f"Plan: {plan}")
        code = read_file("main.py")
        print(f"Git result: {git_push('Update main.py: ' + time.ctime())}")
        prompt = f"Optimize this code:\n{code}"
        grok_response = ask_grok(prompt, headless=args.headless)
        if grok_response and "Failed" not in grok_response:
            print(f"Grok says:\n{grok_response}")
        else:
            print(f"Local says:\n{local_reasoning(prompt)}")

if __name__ == "__main__":
    main()
