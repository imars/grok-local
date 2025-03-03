#!/bin/bash

# Set your Twitter handle
export X_HANDLE="@ianatmars"

# Define profile directory
PROFILE_DIR="/tmp/brave_grok_profile"

# Check if Brave is running on port 9222
if lsof -i :9222 > /dev/null; then
  echo "Brave already running on port 9222. Attaching to existing instance..."
  BRAVE_RUNNING=true
else
  echo "No Brave instance found. Launching new one..."
  BRAVE_RUNNING=false
fi

# Kill and clear only if launching new, preserving cookies
if [ "$BRAVE_RUNNING" = false ]; then
  echo "Killing existing Brave instances..."
  pkill -9 -f "brave_grok_profile" || echo "No instances found to kill."

  # Clear crash logs and session data, preserve cookies
  echo "Clearing crash logs and session data (preserving cookies)..."
  if [ -d "$PROFILE_DIR" ]; then
    find "$PROFILE_DIR" -type f \( -name "Crashpad" -o -name "Sessions" -o -name "Cache" -o -name "*.log" \) -exec rm -rf {} + 2>/dev/null || echo "Warning: Failed to clear some crash/session files in $PROFILE_DIR"
  else
    mkdir -p "$PROFILE_DIR" || { echo "Failed to create profile directory"; exit 1; }
  fi

  # Launch Brave with extension and debugging port
  echo "Launching Brave..."
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    --remote-debugging-port=9222 \
    --load-extension="$(pwd)/memory/grok_chat_logger" \
    --user-data-dir="$PROFILE_DIR" \
    --no-sandbox \
    --remote-debugging-address=127.0.0.1 &
  BRAVE_PID=$!
  echo "Brave launched with PID $BRAVE_PID. Waiting for startup..."
  sleep 5
else
  BRAVE_PID=$(lsof -i :9222 | grep Brave | awk '{print $2}' | head -1)
  echo "Attached to existing Brave with PID $BRAVE_PID."
fi

# Check if Brave is running and port is active
echo "Checking if port 9222 is active..."
if ! lsof -i :9222 > /dev/null; then
  echo "Error: Port 9222 not active. Brave may not have started."
  kill -9 "$BRAVE_PID" 2>/dev/null
  exit 1
fi
echo "Port 9222 is active. Proceeding..."

# Verify extension is enabled
echo "Verifying Grok Chat Logger extension..."
TEMP_OUTPUT=$(mktemp)
node -e "const puppeteer = require('puppeteer');
(async () => {
  try {
    const browser = await puppeteer.connect({ browserURL: 'http://localhost:9222', timeout: 30000 });
    const pages = await browser.pages();
    const page = pages[0];
    await page.goto('brave://extensions/', { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => console.log('Failed to load extensions page, skipping verification.'));
    const enabled = await page.evaluate(() => {
      const ext = document.querySelector('extensions-item[id*=\"grok_chat_logger\"]');
      return ext ? ext.querySelector('input[type=\"checkbox\"]').checked : false;
    }).catch(() => false);
    console.log('Grok Chat Logger enabled:', enabled);
  } catch (e) {
    console.log('Error verifying extension:', e.message);
  } finally {
    process.exit(0);
  }
})()" > "$TEMP_OUTPUT" 2>&1
if [ $? -ne 0 ]; then
  echo "Warning: Extension verification failed or timed out. Output:"
  cat "$TEMP_OUTPUT"
fi
rm -f "$TEMP_OUTPUT"
echo "Extension verification completed (proceeding regardless)."

# Connect Puppeteer and log chats with network retry and fallback
echo "Connecting Puppeteer and starting chat logging..."
node -e 'const puppeteer = require("puppeteer");
(async () => {
  try {
    console.log("Connecting to running Brave instance...");
    const browser = await puppeteer.connect({ browserURL: "http://localhost:9222", timeout: 60000 });
    console.log("Connected successfully!");
    let page;
    let retryCount = 0;
    const maxRetries = 5;

    while (retryCount < maxRetries) {
      const pages = await browser.pages();
      page = pages.find(p => p.url().includes("grok") && p.url().includes("1895083745784254635"));
      if (!page) {
        console.log("Grok chat page not found, opening new tab (attempt $((retryCount + 1)) of $maxRetries)...");
        page = await browser.newPage();
        try {
          await page.goto("https://x.com/i/grok?conversation=1895083745784254635", { waitUntil: "networkidle2", timeout: 120000 });
          break;
        } catch (e) {
          console.log("Network error during navigation:", e.message);
          retryCount++;
          if (retryCount < maxRetries) {
            console.log("Retrying navigation in 15 seconds...");
            await new Promise(resolve => setTimeout(resolve, 15000));
          } else {
            console.log("Max retries reached for navigation. Checking current DOM state.");
            break;
          }
        }
      } else {
        console.log("Reusing existing Grok chat tab...");
        break;
      }
    }

    console.log("On Grok chat page. Current URL:", await page.url());

    console.log("Checking login state...");
    if (!(await page.url()).includes("x.com")) {
      console.log("Not logged in. Please log in manually at https://x.com/i/grok, then navigate to https://x.com/i/grok?conversation=1895083745784254635.");
      console.log("Waiting for manual login...");
      await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });
    } else {
      console.log("Logged in confirmed via cookies!");
    }

    console.log("Debugging DOM for selector 'div.css-175oi2r.r-1f2l425.r-13qz1uu.r-417010'...");
    const initialElements = await page.$$("div.css-175oi2r.r-1f2l425.r-13qz1uu.r-417010");
    console.log("Found", initialElements.length, "elements with the selector.");

    // Fallback selector attempt
    if (initialElements.length === 0) {
      console.log("Fallback: Debugging DOM for alternative selector 'span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3'...");
      const fallbackElements = await page.$$("span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3");
      console.log("Found", fallbackElements.length, "elements with fallback selector.");
    }

    console.log("Type a message (e.g., \"[grok_local] Test\") in the chat and press Enter.");
    console.log("Starting chat logging... (Ctrl+C to stop)");

    // Trap Ctrl+C to exit script without closing browser
    process.on("SIGINT", () => {
      console.log("\nStopping chat logging. Browser remains open.");
      process.exit(0);
    });

    // Initial scan and continuous logging
    async function logMessages() {
      try {
        const messages = await page.evaluate(() => {
          const primaryElements = document.querySelectorAll("div.css-175oi2r.r-1f2l425.r-13qz1uu.r-417010");
          const fallbackElements = document.querySelectorAll("span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3");
          const allElements = [...primaryElements, ...fallbackElements];
          const chats = JSON.parse(localStorage.getItem("grok_chats") || "[]");
          const newChats = [];
          allElements.forEach(el => {
            const text = el.textContent.trim();
            if (text && text.startsWith("[grok_local]") && !chats.some(c => c.text === text)) {
              const project = text.match(/^\[(.*?)\]/)[1] || "unknown";
              newChats.push({ project, text, timestamp: Date.now() });
            }
          });
          if (newChats.length > 0) {
            chats.push(...newChats);
            localStorage.setItem("grok_chats", JSON.stringify(chats));
          }
          return newChats;
        });
        if (messages.length > 0) {
          console.log("Current logged chats:", JSON.stringify(messages, null, 2));
        } else {
          console.log("No new chats logged yet.");
        }
      } catch (e) {
        console.log("Error retrieving chats:", e.message);
      }
    }

    // Initial scan
    await logMessages();

    // Continuous logging
    setInterval(logMessages, 5000);
  } catch (e) {
    console.error("Script failed (browser remains open):", e.message);
    process.exit(0);  // Exit without closing browser
  }
})();'
