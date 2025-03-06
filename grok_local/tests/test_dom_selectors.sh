#!/bin/bash

# Define candidates (based on analyse_dom.sh output)
CANDIDATES=(
  "div.css-175oi2r.r-1f2l425.r-13qz1uu.r-417010"
  "span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3"
  "div.css-146c3p1.r-bcqeeo.r-1ttztb7.r-qvutc0.r-37j5jr.r-a023e6.r-16dba41.r-1kt6imw.r-dnmrzs"
  "div.css-175oi2r.r-1awozwy.r-1fkb3t2.r-1867qdf.r-1ssbvtb.r-zmhzs6.r-11f147o.r-3pj75a"
)

# Base delay (10 seconds) with random addition (0-5 seconds)
DELAY_BASE=10
DELAY_ADDITION=$(shuf -i 0-5 -n 1)
DELAY=$((DELAY_BASE + DELAY_ADDITION))

echo "Starting slow DOM selector test on live Grok chat..."
echo "Testing ${#CANDIDATES[@]} candidates with randomized delays (base $DELAY_BASE + $DELAY_ADDITION = $DELAY seconds)."

# Execute Node.js test script
node -e 'const puppeteer = require("puppeteer");
(async () => {
  console.log("Connecting to running Brave instance...");
  const browser = await puppeteer.connect({ browserURL: "http://localhost:9222", timeout: 30000 });
  console.log("Connected successfully!");

  const page = await browser.newPage();
  console.log("Navigating to Grok chat...");
  await page.goto("https://x.com/i/grok?conversation=1895083745784254635", { waitUntil: "networkidle2", timeout: 60000 });
  console.log("On Grok chat page. Current URL:", await page.url());

  const candidates = process.argv.slice(2);
  for (let i = 0; i < candidates.length; i++) {
    const selector = candidates[i];
    console.log(`\nTesting selector ${i + 1}/${candidates.length}: ${selector}`);
    try {
      const elements = await page.$$eval(selector, els => els.map(el => el.textContent.trim()).filter(t => t));
      if (elements.length > 0) {
        console.log("Found elements:", elements);
        console.log("Selector appears valid. Sample texts:", elements.slice(0, 3));
      } else {
        console.log("No elements found with this selector.");
      }
    } catch (e) {
      console.log("Error testing selector:", e.message);
    }
    if (i < candidates.length - 1) {
      console.log(`Waiting ${process.env.DELAY} seconds before next test...`);
      await new Promise(resolve => setTimeout(resolve, process.env.DELAY * 1000));
    }
  }

  console.log("\nAll tests complete. Browser remains open—review results and proceed.");
  // Removed browser.close() to keep session alive
})()' "${CANDIDATES[@]}"
