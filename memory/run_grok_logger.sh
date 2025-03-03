#!/bin/bash

# Set your Twitter handle
export X_HANDLE="@ianatmars"

# Define profile directory
PROFILE_DIR="/tmp/brave_grok_profile"

# Kill any existing Brave instances for this profile
echo "Killing existing Brave instances..."
pkill -9 -f "brave_grok_profile"

# Clear session data but keep settings
echo "Clearing session data..."
[ -d "$PROFILE_DIR" ] && rm -rf "$PROFILE_DIR"/{Default/Sessions,Default/Cache}

# Launch Brave once to set up profile and disable Shields
if [ ! -d "$PROFILE_DIR" ]; then
  echo "Setting up profile with Shields disabled for x.com..."
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    --user-data-dir="$PROFILE_DIR" \
    --no-sandbox &
  sleep 5
  node -e 'const puppeteer = require("puppeteer");
  (async () => {
    const browser = await puppeteer.launch({
      executablePath: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
      userDataDir: "'"$PROFILE_DIR"'",
      headless: false,
      args: ["--no-sandbox"]
    });
    const page = await browser.newPage();
    await page.goto("brave://settings/shields");
    await page.waitForSelector("#trackersAdsSetting", { timeout: 10000 });
    await page.evaluate(() => { document.querySelector("#trackersAdsSetting").value = "disabled"; });
    await page.goto("https://x.com");
    await browser.close();
  })();'
fi

# Launch Brave with extension and debugging port
echo "Launching Brave..."
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 \
  --load-extension="$(pwd)/memory/grok_chat_logger" \
  --user-data-dir="$PROFILE_DIR" \
  --no-sandbox \
  --remote-debugging-address=127.0.0.1 &

# Wait for Brave to start
sleep 5

# Connect Puppeteer and run the login script
echo "Connecting Puppeteer..."
node -e 'const puppeteer = require("puppeteer");
(async () => {
  console.log("Connecting to Brave...");
  const browser = await puppeteer.connect({ browserURL: "http://localhost:9222" });
  console.log("Connected successfully!");
  const page = await browser.newPage();
  console.log("New page created.");

  console.log("Navigating to X login...");
  await page.goto("https://x.com/i/grok", { waitUntil: "networkidle2", timeout: 60000 });
  console.log("Navigation complete. Current URL:", await page.url());

  console.log("Waiting for login input...");
  await page.waitForSelector("input[name=\"text\"]", { timeout: 15000 });
  await page.type("input[name=\"text\"]", process.env.X_HANDLE);
  console.log("Handle entered:", process.env.X_HANDLE);

  console.log("Looking for Next button...");
  await new Promise(resolve => setTimeout(resolve, 5000));
  const nextButton = await page.waitForSelector("button.r-1ny4l3l", { timeout: 10000 });
  if (!nextButton) {
    console.log("Next button not found. Page content:", await page.content().slice(0, 500));
    process.exit(1);
  }
  await page.evaluate(btn => btn.click(), nextButton);
  console.log("Clicked Next. Current URL:", await page.url());

  console.log("Please enter your password and submit. If 2FA is required, enter that too. Script will wait...");
  await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });
  console.log("Post-password URL:", await page.url());

  // Handle potential 2FA
  const verifyInput = await page.$("input[name=\"verification_code\"]");
  if (verifyInput) {
    console.log("2FA detected. Please enter your code and submit manually.");
    await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });
    console.log("Post-2FA URL:", await page.url());
  }

  // Verify login
  if (!(await page.url()).includes("x.com")) {
    console.log("Login failed. Current URL:", await page.url());
    process.exit(1);
  }
  console.log("Login successful! Navigating to target Grok chat...");
  await page.goto("https://x.com/i/grok?conversation=1895083745784254635", { waitUntil: "networkidle2" });
  console.log("Ready for chats! Final URL:", await page.url());
})();'
