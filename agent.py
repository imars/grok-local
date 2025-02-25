import requests
import git
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

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
  # chrome_options.add_argument("--headless")  # Uncomment later
  print("DEBUG: Initializing ChromeDriver")
  driver = webdriver.Chrome(options=chrome_options)
  print(f"DEBUG: Navigating to {GROK_URL}")
  driver.get(GROK_URL)
  wait = WebDriverWait(driver, 30)

  # Load cookies if they exist
  if os.path.exists(COOKIE_FILE):
      print("DEBUG: Loading cookies")
      cookies = pickle.load(open(COOKIE_FILE, "rb"))
      for cookie in cookies:
          driver.add_cookie(cookie)
      driver.refresh()

  try:
      print("DEBUG: Checking for prompt input")
      prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))
      print("DEBUG: Signed in - sending prompt")
  except:
      print("DEBUG: Sign-in required - please log in manually this time")
      input("DEBUG: Log in manually in the browser, then press Enter here: ")
      pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))
      print("DEBUG: Cookies saved - retrying prompt")
      prompt_box = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "r-30o5oe")))

  try:
      print("DEBUG: Sending prompt to input")
      prompt_box.clear()
      prompt_box.send_keys(prompt)
      print("DEBUG: Looking for submit button")
      submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "css-175oi2r")))
      submit_button.click()
      print("DEBUG: Waiting for response")
      response = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'css-146c3p1') and contains(., 'optimized')]")))
      full_response = response.get_attribute("textContent")  # Use textContent for cleaner output
      print(f"DEBUG: Response received: {full_response}")
      return full_response
  except Exception as e:
      print(f"DEBUG: Error occurred: {e}")
      print(f"DEBUG: Manual fallback - paste this to Grok:\n{prompt}")
      response = input("DEBUG: Enter Grok's response here: ")
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
          "messages": [{"role": "user", "content": f"Plan: {task}"}]
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
  print("DEBUG: Starting main")
  task = "Read main.py and push it to GitHub."
  plan = local_reasoning(task)
  print(f"Plan: {plan}")

  code = read_file("main.py")
  git_result = git_push(f"Update main.py: {time.ctime()}")
  print(f"Git result: {git_result}")

  prompt = f"Optimize this code:\n{code}"
  grok_response = ask_grok(prompt)
  print(f"Grok says: {grok_response}")

if __name__ == "__main__":
  main()
