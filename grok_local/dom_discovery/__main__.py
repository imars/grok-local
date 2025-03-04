import os
from .html_fetcher import fetch_html
from .element_parser import parse_dom_elements
from .agent_analyzer import analyze_elements

def main():
    """Run DOM discovery on a local HTML file."""
    html_path = "grok_com.html"
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found. Please provide a valid HTML file.")
        return

    # Step 1: Fetch HTML
    html_content = fetch_html(html_path)
    if not html_content:
        print("Failed to load HTML")
        return

    # Step 2: Parse elements
    dom_elements = parse_dom_elements(html_content)
    print(f"Parsed {sum(len(v) for v in dom_elements.values())} DOM elements")

    # Step 3: Analyze with DeepSeekAI
    analysis = analyze_elements(dom_elements, html_content, url="https://grok.com")
    print(f"Raw AI Response: {analysis['raw_response']}")
    if analysis['parsed']:
        print("Parsed AI Suggestions:")
        print(json.dumps(analysis['parsed'], indent=2))
    if analysis['error']:
        print(f"Analysis Error: {analysis['error']}")

if __name__ == "__main__":
    main()
