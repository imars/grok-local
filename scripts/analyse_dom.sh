#!/bin/bash

# Install cheerio if not present
if ! npm list cheerio > /dev/null 2>&1; then
  echo "Installing cheerio..."
  npm install cheerio
fi

# Define absolute path to HTML file
HTML_FILE="/Users/ian/dev/projects/agents/local/grok/repo/local/html/grok_chat.html"

# Debug current directory and file existence
echo "Current directory: $(pwd)"
echo "Checking file at: $(realpath "$HTML_FILE" 2>/dev/null || echo "$HTML_FILE")"

# Execute Node.js analysis script
node -e 'const fs = require("fs");
const cheerio = require("cheerio");
const path = require("path");

(() => {
  const htmlFile = "'"$HTML_FILE"'";
  console.log("Resolved HTML file path:", htmlFile);
  if (!fs.existsSync(htmlFile)) {
    console.error("HTML file not found at:", htmlFile);
    process.exit(1);
  }

  console.log("Loading HTML from", htmlFile);
  const html = fs.readFileSync(htmlFile, "utf8");
  const $ = cheerio.load(html);

  console.log("Analyzing DOM for message elements...");
  const candidates = [];

  $("div, span").each((i, elem) => {
    const text = $(elem).text().trim();
    if (text && text.length > 0) {
      const classes = $(elem).attr("class") || "";
      const tag = elem.name;
      if (text.includes("GROK_LOCAL_TEST_CHANNEL") || text.length > 10) {
        candidates.push({
          tag: tag,
          classes: classes,
          text: text.slice(0, 50) + (text.length > 50 ? "..." : ""),
          selector: `${tag}${classes ? "." + classes.replace(/\s+/g, ".") : ""}`
        });
      }
    }
  });

  console.log("\nPotential message element candidates:");
  candidates.forEach((cand, index) => {
    console.log(`Candidate ${index + 1}:`);
    console.log(`  Tag: <${cand.tag}>`);
    console.log(`  Classes: ${cand.classes}`);
    console.log(`  Sample Text: "${cand.text}"`);
    console.log(`  Suggested Selector: ${cand.selector}`);
    console.log("-------------------");
  });

  if (candidates.length > 0) {
    const best = candidates.find(c => c.text.includes("GROK_LOCAL_TEST_CHANNEL")) || candidates[0];
    console.log("\nRecommended Selector: ", best.selector);
    console.log("Note: Test this in content.js. Adjust if it captures too much/noisy content.");
  } else {
    console.log("\nNo suitable message elements found. Check the HTML or try a different file.");
  }
})();'
