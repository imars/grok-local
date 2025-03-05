# grok_local/commands/bridge_commands.py
import logging
import requests
import uuid
import time
from ..utils import report

logger = logging.getLogger(__name__)
BRIDGE_URL = "http://0.0.0.0:5000"

def handle_bridge_command(request, ai_adapter):
    req_lower = request.lower()
    if req_lower.startswith("grok "):
        prompt = request[5:].strip()
        return report(ai_adapter.delegate(prompt))
    elif req_lower.startswith("send to grok "):
        message = request[12:].strip()
        req_id = str(uuid.uuid4())
        try:
            response = requests.post(f"{BRIDGE_URL}/channel", json={"input": message, "id": req_id}, timeout=5)
            if response.status_code != 200:
                logger.error(f"Bridge POST failed: {response.text}")
                return report(f"Failed to send to Grok: {response.text}")
            # Poll for response
            max_attempts = 10
            delay = 2  # seconds
            for attempt in range(max_attempts):
                resp = requests.get(f"{BRIDGE_URL}/get-response", params={"id": req_id}, timeout=5)
                if resp.status_code == 200:
                    return report(f"Grok response: {resp.text}")
                elif resp.status_code != 404:
                    logger.error(f"Bridge GET failed: {resp.text}")
                    return report(f"Error fetching response: {resp.text}")
                logger.info(f"Waiting for Grok response (attempt {attempt + 1}/{max_attempts})")
                time.sleep(delay)
            return report("No response from Grok within timeout")
        except requests.RequestException as e:
            logger.error(f"Bridge connection failed: {e}")
            return report(f"Error: Could not connect to bridge at {BRIDGE_URL}")
    else:
        return f"Unknown bridge command: {request}"
