# grok_local/dom_discovery/ollama_manager.py
import requests
import subprocess
import time
import logging
from grok_local.config import logger

def ensure_ollama_running(model):
    """Ensure Ollama is running and the model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json()["models"]]
            if f"{model}:latest" not in models:
                logger.info(f"Pulling model {model}...")
                subprocess.run(["ollama", "pull", model], check=True)
            logger.info("Ollama is running and model is available")
            return True
    except (requests.ConnectionError, subprocess.CalledProcessError):
        logger.info("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"])
        time.sleep(5)
        try:
            logger.info(f"Pulling model {model}...")
            subprocess.run(["ollama", "pull", model], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull model {model}: {str(e)}")
            return False
    return False
