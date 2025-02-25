import requests
import git
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json

# Config
PROJECT_DIR = os.getcwd()
REPO_URL = "git@github.com:imars/grok-local.git"
MODEL = "deepseek-r1:8b"
OLLAMA_URL = "http://localhost:11434"  # Matches your Ollama app’s API port
GROK_URL = "https://www.google.com"  # Placeholder; replace with Grok URL

def git_push(message="Automated commit"):
    print(f"DEBUG: Starting git_push with message: {message}")
    repo = git.Repo(PROJECT_DIR)
    repo.git.add(A=True)
    print("DEBUG: Files staged")
    repo.git.commit(m=message)
    print("DEBUG: Commit made")
    repo.git.push()
    print("DEBUG: Push completed")
    return "Pushed to GitHub"

def read_file(filename):
    print(f"DEBUG: Reading file: {filename}")
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "r") as f:
        content = f.read()
    print(f"DEBUG: File read: {content}")
    return content

def ask_grok(prompt):
    print(f"DEBUG: Starting ask_grok with prompt: {prompt}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    print("DEBUG: Initializing ChromeDriver")
    driver = webdriver.Chrome(options=chrome_options)
    print(f"DEBUG: Navigating to {GROK_URL}")
    driver.get(GROK_URL)
    print("DEBUG: Waiting for page load")
    time.sleep(2)
    
    try:
        print("DEBUG: Looking for prompt input")
        prompt_box = driver.find_element(By.ID, "prompt-input")
        print("DEBUG: Sending prompt to input")
        prompt_box.send_keys(prompt)
        print("DEBUG: Looking for submit button")
        driver.find_element(By.ID, "submit-button").click()
        print("DEBUG: Waiting for response")
        time.sleep(3)
        print("DEBUG: Fetching response")
        response = driver.find_element(By.ID, "response-output").text
        print(f"DEBUG: Response received: {response}")
    except Exception as e:
        response = f"Error interacting with Grok: {e}"
        print(f"DEBUG: Error occurred: {response}")
    finally:
        print("DEBUG: Closing browser")
        driver.quit()
    return response

def local_reasoning(task):
    print(f"DEBUG: Starting local_reasoning with task: {task}")
    try:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": f"Perform this task: {task}"}]
        }
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        result = json.loads(response.text)["message"]["content"]
        print(f"DEBUG: Local reasoning result: {result}")
    except requests.exceptions.RequestException as e:
        result = f"Ollama error: {e}"
        print(f"DEBUG: Local reasoning failed: {result}")
    return result

def main():
    print("DEBUG: Starting main")
    task = "Read main.py, push it to GitHub, and ask Grok for optimization suggestions."
    plan = local_reasoning(task)
    print(f"Plan: {plan}")

    code = read_file("main.py")
    git_result = git_push(f"Update main.py: {time.ctime()}")
    print(f"Git result: {git_result}")

    prompt = f"Optimize this code:\n{code}"
    grok_response = ask_grok(prompt)
    print(f"Grok says: {grok_response}")

    next_steps = local_reasoning(f"Grok suggested: {grok_response}. What should I do next?")
    print(f"Next steps: {next_steps}")

if __name__ == "__main__":
    main()
