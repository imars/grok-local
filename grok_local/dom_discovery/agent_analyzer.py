import json
import logging
from grok_local.config import logger
from grok_local.ai_adapters.deepseek_ai import DeepSeekAI

def analyze_elements(dom_elements, html_content, url="unknown", model="deepseek-chat"):
    """Analyze DOM elements to identify navigation candidates and agent roles with DeepSeekAI."""
    # Step 1: Prepare elements (add candidate_role if missing)
    elements_with_roles = []
    for elem_type, elements in dom_elements.items():
        for elem in elements:
            # Default confidence if not present
            if "candidate_role" not in elem:
                elem["candidate_role"] = {"role": "unknown", "confidence": 0.5}
            elem["type"] = elem_type  # Track element type (button, input, etc.)
            elements_with_roles.append(elem)

    # Step 2: Get top elements by confidence (or default sorting)
    top_elements = sorted(elements_with_roles, key=lambda x: x["candidate_role"]["confidence"], reverse=True)[:5]
    
    # Step 3: Build prompt for DeepSeekAI
    deepseek = DeepSeekAI()
    prompt = (
        f"Analyze this HTML snippet from {url}:\n\n{html_content[:1000]}\n\n"
        f"Here are the top detected elements:\n{json.dumps(top_elements, indent=2)}\n\n"
        "Suggest the best candidates for:\n"
        "- Prompt input (where to enter text)\n"
        "- Submit button (to send the prompt)\n"
        "- Response output (where the answer appears)\n"
        "Provide selectors (e.g., '#id', '.class', or tag) and reasoning in JSON format like:\n"
        "{\n"
        "  \"prompt_input\": {\"selector\": \"#input-id\", \"reason\": \"...\"},\n"
        "  \"submit_button\": {\"selector\": \".btn\", \"reason\": \"...\"},\n"
        "  \"response_output\": {\"selector\": \"#output\", \"reason\": \"...\"}\n"
        "}"
    )

    # Step 4: Delegate to DeepSeekAI and parse response
    try:
        logger.info("Sending prompt to DeepSeekAI")
        raw_response = deepseek.delegate(prompt)
        logger.info(f"DeepSeekAI response: {raw_response}")

        # Attempt to parse JSON response
        try:
            suggestions = json.loads(raw_response)
            if not all(k in suggestions for k in ["prompt_input", "submit_button", "response_output"]):
                logger.warning("Incomplete JSON response from DeepSeekAI")
                return {"raw_response": raw_response, "parsed": None, "error": "Incomplete JSON"}
        except json.JSONDecodeError:
            logger.warning("DeepSeekAI response is not valid JSON")
            return {"raw_response": raw_response, "parsed": None, "error": "Invalid JSON"}

        return {
            "raw_response": raw_response,
            "parsed": suggestions,
            "error": None
        }
    except Exception as e:
        logger.error(f"DeepSeekAI analysis failed: {str(e)}")
        return {"raw_response": None, "parsed": None, "error": str(e)}

if __name__ == "__main__":
    # Test with sample data
    with open("grok_elements.json", 'r', encoding='utf-8') as f:
        dom_elements = json.load(f)
    with open("grok_com.html", 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    result = analyze_elements(dom_elements, html_content, url="https://grok.com")
    print(f"Raw Response: {result['raw_response']}")
    if result['parsed']:
        print("Parsed Suggestions:")
        print(json.dumps(result['parsed'], indent=2))
    if result['error']:
        print(f"Error: {result['error']}")
