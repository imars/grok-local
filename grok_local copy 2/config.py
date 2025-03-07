# grok_local/config.py
import os
import logging
from dotenv import load_dotenv

# Project paths
PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")
LOCAL_DIR = os.path.join(PROJECT_DIR, "local")

# Load environment variables
load_dotenv()
GROK_USERNAME = os.getenv("GROK_USERNAME")
GROK_PASSWORD = os.getenv("GROK_PASSWORD")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
AI_BACKEND = os.getenv("AI_BACKEND", "STUB")  # Default to stub
BROWSER_BACKEND = os.getenv("BROWSER_BACKEND", "PLAYWRIGHT")  # Default to Playwright

# Logger initialized here, but configured in main.py
logger = logging.getLogger(__name__)
