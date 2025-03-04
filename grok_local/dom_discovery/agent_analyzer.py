# grok_local/dom_discovery/agent_analyzer.py
import json
import logging
from grok_local.config import logger
from grok_local.ai_adapters import get_ai_adapter

def get_agent_suggestions(url, html, elements, model):
    """Get agent suggestions for DOM element roles."""
    agent = get_ai_adapter("LOCAL_DEEPSEEK", model=model)
    top_elements = sorted(elements, key=lambda x: x["candidate_role"]["confidence"], reverse=True)[:5]
    prompt = (
        f"Analyze this HTML snippet from {url}:\n\n{html[:1000]}\n\n"
        f"Here are the top detected elements:\n{json.dumps(top_elements, indent=2)}\n\n"
        "Suggest the best candidates for:\n"
        "- Prompt input (where to enter text)\n"
        "- Submit button (to send the prompt)\n"
        "- Response output (where the answer appears)\n"
        "Provide selectors and reasoning in JSON format."
    )
    try:
        logger.info("Sending prompt to agent")
        response = agent.delegate(prompt)
        logger.info(f"Agent suggestions: {response}")
        return {"raw_response": response}
    except Exception as e:
        logger.error(f"Agent analysis failed: {str(e)}")
        return {"error": str(e)}
