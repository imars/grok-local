const puppeteer = require("puppeteer");

(async () => {
  console.log("Connecting to Brave...");
  const browser = await puppeteer.connect({
    browserURL: "http://localhost:9222"
  });
  console.log("Connected successfully!");

  const page = await browser.newPage();
  console.log("New page created.");

  console.log("Navigating to X login...");
  await page.goto("https://x.com/i/grok", { waitUntil: "networkidle2", timeout: 60000 });
  console.log("Navigation complete. Current URL:", await page.url());

  console.log("Waiting for login input...");
  await page.waitForSelector('input[name="text"]', { timeout: 15000 });
  const handle = process.env.X_HANDLE || "your_twitter_handle";
  await page.type('input[name="text"]', handle);
  console.log("Handle entered:", handle);

  console.log("Looking for Next button...");
  await new Promise(resolve => setTimeout(resolve, 5000));
  const selectors = [
    'button.r-1udbk01',
    'button.r-1ny4l3l',
    'button:contains("Next")'
  ];

  let nextButton;
  for (const selector of selectors) {
    try {
      if (selector.includes(":contains")) {
        nextButton = await page.evaluateHandle(text => {
          const buttons = Array.from(document.querySelectorAll("button"));
          return buttons.find(btn => btn.textContent.includes("Next"));
        }, "Next");
      } else {
        nextButton = await page.$(selector);
      }
      if (nextButton) {
        console.log("Found Next button with selector:", selector);
        break;
      }
    } catch (e) {
      console.log("Selector failed:", selector, e.message);
    }
  }

  if (!nextButton) {
    console.log("No Next button found. Page content:", await page.content().slice(0, 500));
    throw new Error("Next button not located");
  }
  await page.evaluate(btn => btn.click(), nextButton);
  console.log("Clicked Next. Current URL:", await page.url());

  console.log("Please enter your password and log in. Script will wait...");
  await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });
  console.log("Post-password URL:", await page.url());

  // Check for 2FA or additional steps
  const verifyInput = await page.$('input[name="verification_code"]');
  if (verifyInput) {
    console.log("2FA detected. Please enter your verification code and submit manually.");
    await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 0 });
    console.log("Post-2FA URL:", await page.url());
  }

  console.log("Logged in! Opening Grok chat page...");
  await page.goto("https://grok.com", { waitUntil: "networkidle2" });
  console.log("Ready for chats! Final URL:", await page.url());
})();
