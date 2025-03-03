#!/bin/bash

# Set your Twitter handle (for reference, not login)
X_HANDLE="@ianatmars"

# Define profile directory and HTML file path with validation
PROFILE_DIR="/tmp/brave_grok_profile"
HTML_FILE="/Users/ian/dev/projects/agents/local/grok/repo/local/html/grok_chat.html"

# Debugging: Start with environment info
echo "Starting end-to-end test at \$(date)"
echo "Current directory: \$(pwd)"
echo "Profile directory: $PROFILE_DIR"
echo "HTML file path: $HTML_FILE"

# Validate profile directory
if [ -z "$PROFILE_DIR" ] || [ ! -d "$PROFILE_DIR" ] && ! mkdir -p "$PROFILE_DIR" 2>/dev/null; then
  echo "Error: Invalid or inaccessible profile directory: $PROFILE_DIR"
  exit 1
fi

# Check if Brave is already running on port 9222
if lsof -i :9222 > /dev/null; then
  echo "Brave already running on port 9222. Attaching to existing instance..."
  BRAVE_RUNNING=true
else
  echo "No Brave instance found. Launching new one..."
  BRAVE_RUNNING=false
fi

# Kill any existing Brave instances for this profile if launching new
if [ "$BRAVE_RUNNING" = false ]; then
  echo "Killing existing Brave instances..."
  pkill -9 -f "brave_grok_profile" || echo "No instances found to kill."

  # Clear all profile data to ensure no crash logs or restore prompts
  echo "Clearing all profile data..."
  if [ -d "$PROFILE_DIR" ]; then
    rm -rf "$PROFILE_DIR"/* 2>/dev/null || echo "Warning: Failed to clear some files in $PROFILE_DIR (permission denied?)"
  else
    mkdir -p "$PROFILE_DIR" || { echo "Failed to create profile directory"; exit 1; }
  fi

  # Launch Brave with extension and debugging port
  echo "Launching Brave with debugging port 9222..."
  BRAVE_CMD="/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9222 --load-extension=\"\$(pwd)/memory/grok_chat_logger\" --user-data-dir=\"$PROFILE_DIR\" --no-sandbox --remote-debugging-address=127.0.0.1 --no-first-run --no-default-browser-check"
  eval "$BRAVE_CMD" &
  BRAVE_PID=$!
  echo "Brave launched with PID $BRAVE_PID. Waiting for startup..."
  sleep 5

  # Check if Brave is running and port is active
  echo "Checking if port 9222 is active..."
  if ! lsof -i :9222 > /dev/null; then
    echo "Error: Port 9222 not active. Brave may not have started."
    kill -9 "$BRAVE_PID" 2>/dev/null
    exit 1
  fi
  echo "Port 9222 is active. Proceeding..."
fi

# Verify extension is enabled with timeout
echo "Verifying Grok Chat Logger extension (with 30-second timeout)..."
TEMP_OUTPUT=$(mktemp)
node -e "const puppeteer = require('puppeteer');
(async () => {
  try {
    const browser = await puppeteer.connect({ browserURL: 'http://localhost:9222', timeout: 30000 });
    const pages = await browser.pages();
    const page = pages[0];
    console.log('Navigating to extensions page...');
    await page.goto('brave://extensions/', { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => console.log('Failed to load extensions page, skipping verification.'));
    console.log('Checking extension state...');
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

# Save the Grok chat page HTML with retry and extended timeout
echo "Saving Grok chat page HTML (with retry)..."
START_TIME=$(date +%s)
MAX_RETRIES=5
for ((i=1; i<=MAX_RETRIES; i++)); do
  TEMP_OUTPUT=$(mktemp)
  node -e "const puppeteer = require('puppeteer');
  (async () => {
    console.log('Connecting to Brave (attempt $i)...');
    const browser = await puppeteer.connect({ browserURL: 'http://localhost:9222', timeout: 60000 });
    console.log('Connected successfully!');
    const page = await browser.newPage();
    console.log('Navigating to Grok chat...');
    await page.goto('https://x.com/i/grok?conversation=1895083745784254635', { waitUntil: 'networkidle2', timeout: 120000 });
    console.log('Saving page content...');
    const html = await page.content();
    require('fs').writeFileSync('$HTML_FILE', html);
    console.log('HTML saved to', '$HTML_FILE');
    process.exit(0);
  })()" > "$TEMP_OUTPUT" 2>&1
  EXIT_CODE=$?
  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))
  if [ $EXIT_CODE -eq 0 ]; then
    rm -f "$TEMP_OUTPUT"
    echo "HTML save completed successfully on attempt $i (took $DURATION seconds)."
    break
  else
    echo "Failed to save HTML on attempt $i (took $DURATION seconds). Output:"
    cat "$TEMP_OUTPUT"
    rm -f "$TEMP_OUTPUT"
    if [ $i -lt $MAX_RETRIES ]; then
      echo "Retrying in 15 seconds (attempt $((i+1)) of $MAX_RETRIES)..."
      sleep 15
    else
      echo "Max retries ($MAX_RETRIES) reached. Aborting HTML save."
      kill -9 "$BRAVE_PID" 2>/dev/null
      exit 1
    fi
  fi
done

# Analyze the saved HTML for candidates
echo "Analyzing saved HTML for message element candidates..."
if ! npm list cheerio > /dev/null 2>&1; then
  echo "Installing cheerio..."
  npm install cheerio
fi
START_TIME=$(date +%s)
TEMP_OUTPUT=$(mktemp)
node -e "const fs = require('fs');
const cheerio = require('cheerio');
const path = require('path');
(() => {
  console.log('Loading HTML from', '$HTML_FILE');
  const html = fs.readFileSync('$HTML_FILE', 'utf8');
  const \$ = cheerio.load(html);
  console.log('Analyzing DOM...');
  const candidates = [];
  \$('div, span').each((i, elem) => {
    const text = \$(elem).text().trim();
    if (text && text.length > 0) {
      const classes = \$(elem).attr('class') || '';
      const tag = elem.name;
      if (text.includes('GROK_LOCAL_TEST_CHANNEL') || text.length > 10) {
        candidates.push({
          tag: tag,
          classes: classes,
          text: text.slice(0, 50) + (text.length > 50 ? '...' : ''),
          selector: \`\${tag}\${classes ? '.' + classes.replace(/\\s+/g, '.') : ''}\`
        });
      }
    }
  });
  console.log('\nPotential message element candidates:');
  candidates.forEach((cand, index) => {
    console.log(\`Candidate \${index + 1}:\`);
    console.log(\`  Tag: <\${cand.tag}>\`);
    console.log(\`  Classes: \${cand.classes}\`);
    console.log(\`  Sample Text: "\${cand.text}"\`);
    console.log(\`  Suggested Selector: \${cand.selector}\`);
    console.log('-------------------');
  });
  if (candidates.length > 0) {
    const best = candidates.find(c => c.text.includes('GROK_LOCAL_TEST_CHANNEL')) || candidates[0];
    console.log('\nRecommended Selector: ', best.selector);
    process.env.RECOMMENDED_SELECTOR = best.selector;
    process.exit(0);
  } else {
    console.log('\nNo suitable message elements found.');
    process.exit(1);
  }
})()" > "$TEMP_OUTPUT" 2>&1
EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
if [ $EXIT_CODE -ne 0 ]; then
  echo "Failed to analyze HTML (took $DURATION seconds). Output:"
  cat "$TEMP_OUTPUT"
  kill -9 "$BRAVE_PID" 2>/dev/null
  rm -f "$TEMP_OUTPUT"
  exit 1
fi
rm -f "$TEMP_OUTPUT"
echo "HTML analysis completed successfully (took $DURATION seconds)."

# Test the recommended selector on the live DOM with randomized delay
echo "Testing recommended selector on live DOM..."
CANDIDATES=("\$RECOMMENDED_SELECTOR")
DELAY_BASE=10
DELAY_ADDITION=$((RANDOM % 6))  # POSIX-compliant random 0-5
DELAY=$((DELAY_BASE + DELAY_ADDITION))
echo "Testing with delay: $DELAY seconds"
START_TIME=$(date +%s)
TEMP_OUTPUT=$(mktemp)
node -e "const puppeteer = require('puppeteer');
(async () => {
  console.log('Connecting to live Brave instance...');
  const browser = await puppeteer.connect({ browserURL: 'http://localhost:9222', timeout: 30000 });
  console.log('Connected successfully!');
  const pages = await browser.pages();
  let page = pages.find(p => p.url().includes('grok') && p.url().includes('1895083745784254635'));
  if (!page) {
    console.log('No existing Grok chat tab found, creating new page...');
    page = await browser.newPage();
    await page.goto('https://x.com/i/grok?conversation=1895083745784254635', { waitUntil: 'networkidle2', timeout: 120000 });
  } else {
    console.log('Reusing existing Grok chat tab...');
  }
  console.log('Checking login state...');
  if (!(await page.url()).includes('x.com')) {
    console.log('Not logged in. Please log in manually at https://x.com/i/grok, then navigate to https://x.com/i/grok?conversation=1895083745784254635.');
    console.log('Waiting for manual login...');
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 0 });
  } else {
    console.log('Logged in confirmed via cookies!');
  }
  console.log('Testing selector:', process.env.RECOMMENDED_SELECTOR);
  try {
    const elements = await page.\$\$eval(process.env.RECOMMENDED_SELECTOR, els => els.map(el => el.textContent.trim()).filter(t => t));
    if (elements.length > 0) {
      console.log('Found elements:', elements);
      console.log('Selector appears valid. Sample texts:', elements.slice(0, 3));
    } else {
      console.log('No elements found with this selector.');
    }
  } catch (e) {
    console.log('Error testing selector:', e.message);
  }
  console.log('Live DOM test complete. Browser remains open.');
  process.exit(0);
})()" "\${CANDIDATES[@]}" > "$TEMP_OUTPUT" 2>&1
EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
if [ $EXIT_CODE -ne 0 ]; then
  echo "Failed to test live DOM (took $DURATION seconds). Output:"
  cat "$TEMP_OUTPUT"
  rm -f "$TEMP_OUTPUT"
  exit 1
fi
rm -f "$TEMP_OUTPUT"
echo "Live DOM test completed successfully (took $DURATION seconds)."

# End script, leaving browser running
echo "End-to-end test completed at \$(date). Browser left running for manual inspection."
exit 0
