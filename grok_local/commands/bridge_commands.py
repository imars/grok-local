from ..tools.logging import log_conversation
from ..grok_bridge import fetch_response
import requests

def handle_bridge_command(command, ai_adapter):
    question = command.strip()
    if not question:
        return "No question provided for bridge."
    
    try:
        resp = requests.post("http://0.0.0.0:5000/ask", json={"question": question}, timeout=5)
        if resp.status_code != 200:
            return f"Bridge error: {resp.text}"
        
        request_id = resp.json()['id']
        log_conversation(f"Bridge request posted with ID: {request_id}")
        
        response = fetch_response(request_id, timeout=25)
        return f"Bridge response: {response}"
    except requests.Timeout:
        return "Bridge request timed out."
    except Exception as e:
        return f"Bridge failed: {str(e)}"
