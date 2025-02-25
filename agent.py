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

# Config
PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
GROK_URL = "https://x.com/i/grok?conversation=1894190038096736744"
COOKIE_FILE = os.path.join(PROJECT_DIR, "cookies.pkl")

def git_push(message="Automated commit"):
    print(f"DEBUG: Starting git_push with message: {message}")
    repo = git.Repo(PROJECT_DIR)
    repo.git.add(A=True)
    print("DEBUG: Files staged")
    try:
        repo.git.commit(m=message)
        print("DEBUG: Commit made")
    except GitCommandError as e:
        if "nothing to commit" in str(e):
            print("DEBUG: No changes to commit - proceeding")
        else:
            raise
    repo.git.push()
    print("DEBUG: Push completed")
    return "Pushed to GitHub or already up-to-date"

def read_file(filename):
    print(f"DEBUG: Reading file: {filename}")
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        content = f.read()
    print(f"DEBUG: File read: {content}")
    return content

def get_multiline_input(prompt):
    print(prompt)
    print("DEBUG: Paste response below, then press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows):")
    response = sys.stdin.read()
    return response.strip()

def ask_grok(prompt, headless=False):
    print(f"DEBUG: Starting ask_grok with prompt: {prompt}, headless={headless}")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        print("DEBUG: Initializing ChromeDriver (headless)")
    else:
        print("DEBUG: Initializing ChromeDriver (GUI mode)")
    driver = webdriver.Chrome(options=chrome_options)
    print(f"DEBUG: Navigating to {GROK_URL}")
    driver.get(GROK_URL)
    wait = WebDriverWait(driver, 90)

    if os.path.exists(COOKIE_FILE):
        print("DEBUG: Loading cookies")
        cookies = pickle.load(open(COOKIE_FILE, "rb"))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                print("DEBUG: Invalid cookie detected")
        driver.refresh()
    else:
        print("DEBUG: No cookies found - need initial login")
        if headless:
            driver.quit()
            return "Run without --headless first to save cookies, then retry"

    try:
        print("DEBUG: Checking for prompt input")
        prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        print("DEBUG: Signed in - proceeding")
    except:
        print("DEBUG: Sign-in required or cookies invalid")
        driver.get("https://x.com/login")
        if headless:
            driver.quit()
            return "Cookies failed - run without --headless to re-login and verify"
        input("DEBUG: Log in with @ianatmars, then press Enter: ")
        try:
            verify_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='text']")))
            verify_value = input("DEBUG: Enter phone (e.g., +1...) or email for verification: ")
            verify_input.send_keys(verify_value)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            print("DEBUG: Verification submitted")
            time.sleep(5)
        except:
            print("DEBUG: No verification prompt detected")
        driver.get(GROK_URL)
        prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
        print("DEBUG: Signed in - proceeding")
    pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))
    print("DEBUG: Cookies saved")

    try:
        print("DEBUG: Sending prompt to input")
        prompt_box.clear()
        prompt_box.send_keys(prompt)
        print("DEBUG: Looking for submit button")
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
        submit_button.click()
        print("DEBUG: Waiting for response")
        time.sleep(30)  # Increased wait
        initial_count = len(driver.find_elements(By.CLASS_NAME, "css-146c3p1"))
        wait.until(lambda driver: len(driver.find_elements(By.CLASS_NAME, "css-146c3p1")) > initial_count)
        responses = driver.find_elements(By.CLASS_NAME, "css-146c3p1")
        for i, r in enumerate(responses):
            text = r.get_attribute("textContent")
            print(f"DEBUG: Response candidate {i}: {text[:100]}...")
            if "optimized" in text.lower() or "here" in text.lower() or "greet" in text.lower():
                full_response = text
                break
        else:
            raise Exception("No response with 'optimized', 'here', or 'greet' found")
        print(f"DEBUG: Response received: {full_response}")
        return full_response
    except Exception as e:
        print(f"DEBUG: Error occurred: {e}")
        with open("page_source.html", "w") as f:
            f.write(driver.page_source)  # Full source for debugging
        print("DEBUG: Full page source saved to page_source.html")
        print(f"DEBUG: Manual fallback - paste this to Grok:\n{prompt}")
        response = get_multiline_input("DEBUG: Enter Grok's response here:")
        print(f"DEBUG: Grok replied: {response}")
        return response
    finally:
        print("DEBUG: Closing browser")
        driver.quit()

def local_reasoning(task):
    print(f"DEBUG: Starting local_reasoning with task: {task}")
    try:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": f"Briefly summarize steps to {task}"}]
        }
        print(f"DEBUG: Sending request to {OLLAMA_URL}/api/chat")
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        full_response = ""
        print("DEBUG: Receiving streamed response")
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                if "message" in chunk and "content" in chunk["message"]:
                    full_response += chunk["message"]["content"]
                    print(f"DEBUG: Chunk received after {time.time() - start_time:.2f}s: {chunk['message']['content']}")
                if chunk.get("done", False):
                    print(f"DEBUG: Stream completed after {time.time() - start_time:.2f}s")
                    break
        print(f"DEBUG: Local reasoning result: {full_response}")
        return full_response
    except requests.exceptions.RequestException as e:
        result = f"Ollama error: {e}"
        print(f"DEBUG: Local reasoning failed: {result}")
        return result

def main():
    parser = argparse.ArgumentParser(description="Run the agent with optional headless mode")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    args = parser.parse_args()

    print("DEBUG: Starting main")
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
