const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

(async () => {
  const bravePath = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
  const extensionPath = path.resolve(__dirname, "grok_chat_logger");
  const userDataDir = "/tmp/brave_grok_profile";

  if (!fs.existsSync(extensionPath)) {
    console.log("Extension not found. Creating it...");
    createExtension(extensionPath);
  } else {
    console.log("Extension exists. Ensuring permissions...");
    fs.chmodSync(extensionPath, "755");
    fs.readdirSync(extensionPath).forEach(file => fs.chmodSync(path.join(extensionPath, file), "644"));
  }

  console.log("Starting Brave manually...");
  const braveCmd = `"${bravePath}" --remote-debugging-port=9222 --load-extension=${extensionPath} --user-data-dir=${userDataDir} --no-sandbox`;
  exec(braveCmd, (err, stdout, stderr) => {
    if (err) console.log("Manual launch error:", err, stderr);
    else console.log("Brave stdout:", stdout);
  });

  console.log("Waiting for Brave to start (10s)...");
  await new Promise(resolve => setTimeout(resolve, 10000)); // Give Brave time to open

  console.log("Connecting to Brave...");
  let browser;
  try {
    browser = await puppeteer.connect({
      browserURL: "http://localhost:9222",
      timeout: 30000
    });
  } catch (e) {
    console.log("Connection failed:", e.message);
    process.exit(1);
  }
  console.log("Connected to Brave successfully!");

  const page = await browser.newPage();
  console.log("New page created.");

  console.log("Navigating to X login...");
  await page.goto("https://x.com/i/grok", { waitUntil: "networkidle2", timeout: 60000 });
  console.log("Navigated to X login successfully.");

  console.log("Waiting for login input...");
  await page.waitForSelector('input[name="text"]', { timeout: 15000 });
  console.log("Found login input.");

  const handle = process.env.X_HANDLE || "your_twitter_handle";
  await page.type('input[name="text"]', handle);
  await page.click('button[type="submit"]');
  console.log("Handle filled, clicked Next.");

  console.log("Please enter your password and log in. Script will wait...");
  await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });

  console.log("Logged in! Opening Grok chat page...");
  await page.goto("https://grok.com", { waitUntil: "networkidle2" });

  console.log("Browser is ready. Open Grok tabs as needed—the extension will log automatically.");
  // await browser.close();
})();

function createExtension(dir) {
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, "manifest.json"),
    JSON.stringify({
      "manifest_version": 3,
      "name": "Grok Chat Logger",
      "version": "1.0",
      "description": "Logs Grok chats automatically",
      "permissions": ["storage", "activeTab"],
      "content_scripts": [{
        "matches": ["https://*.grok.com/*"],
        "js": ["content.js"],
        "run_at": "document_idle"
      }],
      "icons": {
        "16": "icon16.png",
        "48": "icon48.png",
        "128": "icon128.png"
      }
    }, null, 2)
  );
  fs.writeFileSync(
    path.join(dir, "content.js"),
    "let chats = JSON.parse(localStorage.getItem('grok_chats') || '[]');\n" +
    "function logChat() {\n" +
    "  const messages = Array.from(document.querySelectorAll('.message'));\n" +
    "  messages.forEach(msg => {\n" +
    "    const text = msg.textContent.trim();\n" +
    "    if (text && !chats.some(c => c.text === text)) {\n" +
    "      const project = text.match(/^\\[(.*?)\\]/)?.[1] || 'unknown';\n" +
    "      chats.push({ project, text, timestamp: Date.now() });\n" +
    "      localStorage.setItem('grok_chats', JSON.stringify(chats));\n" +
    "      console.log('Logged:', text);\n" +
    "    }\n" +
    "  });\n" +
    "}\n" +
    "const observer = new MutationObserver(logChat);\n" +
    "observer.observe(document.body, { childList: true, subtree: true });\n" +
    "logChat();"
  );
  const iconData = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==";
  ["icon16.png", "48.png", "128.png"].forEach(file => {
    fs.writeFileSync(path.join(dir, file), Buffer.from(iconData.split(",")[1], "base64"));
    fs.chmodSync(path.join(dir, file), "644");
  });
  fs.chmodSync(dir, "755");
}
