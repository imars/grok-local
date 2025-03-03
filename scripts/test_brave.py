from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import sys

def test_brave_browser():
    # Define paths
    driver_path = "/usr/local/bin/chromedriver"
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    
    # Initialize browser with options
    try:
        print("Initializing Brave browser...")
        option = webdriver.ChromeOptions()
        option.binary_location = brave_path
        # Uncomment these for additional testing
        # option.add_argument("--incognito")
        # option.add_argument("--headless")
        
        # Use Service object instead of executable_path
        service = Service(executable_path=driver_path)
        browser = webdriver.Chrome(service=service, options=option)
        print("✓ Browser initialized successfully")
        
    except Exception as e:
        print(f"✗ Failed to initialize browser: {str(e)}")
        sys.exit(1)
    
    # Test 1: Load a webpage
    try:
        print("\nTest 1: Loading Google...")
        browser.get("https://www.google.es")
        time.sleep(2)  # Wait for page to load
        if "google" in browser.current_url.lower():
            print("✓ Successfully loaded Google")
        else:
            print("✗ Failed to load Google correctly")
    except Exception as e:
        print(f"✗ Test 1 failed: {str(e)}")
    
    # Test 2: Perform a search
    try:
        print("\nTest 2: Performing a search...")
        search_box = browser.find_element(By.NAME, "q")
        search_box.send_keys("Brave Browser Test" + Keys.RETURN)
        time.sleep(2)  # Wait for results
        if "search" in browser.current_url.lower():
            print("✓ Search completed successfully")
        else:
            print("✗ Search test failed")
    except Exception as e:
        print(f"✗ Test 2 failed: {str(e)}")
    
    # Test 3: Get page title
    try:
        print("\nTest 3: Checking page title...")
        title = browser.title
        print(f"✓ Current page title: {title}")
    except Exception as e:
        print(f"✗ Test 3 failed: {str(e)}")
    
    # Cleanup
    try:
        print("\nClosing browser...")
        browser.quit()
        print("✓ Test completed and browser closed")
    except Exception as e:
        print(f"✗ Failed to close browser: {str(e)}")

if __name__ == "__main__":
    print("Starting Brave Browser Test Script")
    print("==================================")
    test_brave_browser()
    print("==================================")
    print("Test script finished")