#!/usr/bin/env node
const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

(async () => {
  console.log("Connecting to running Brave instance...");
  const browser = await puppeteer.connect({
    browserURL: "http://localhost:9222",
    timeout: 30000
  });
  console.log("Connected successfully!");

  const pages = await browser.pages();
  let page = pages.find(p => p.url().includes("grok"));
  if (!page) {
    console.log("Grok chat page not found, opening new tab...");
    page = await browser.newPage();
    await page.goto("https://x.com/i/grok?conversation=1895083745784254635", { waitUntil: "networkidle2", timeout: 60000 });
  }
  console.log("Saving Grok chat page...");

  const html = await page.content();
  const filePath = path.join(__dirname, "..", "local", "html", "grok_chat.html");
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, html);
  console.log("Page saved to local/html/grok_chat.html");

  await browser.close();
  console.log("Done. Check local/html/grok_chat.html.");
})();
