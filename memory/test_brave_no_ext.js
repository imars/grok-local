const puppeteer = require("puppeteer");

(async () => {
  const bravePath = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
  const userDataDir = "/tmp/brave_test_profile"; // Isolated profile
  const browser = await puppeteer.launch({
    executablePath: bravePath,
    headless: false,
    args: [
      "--remote-debugging-port=9222",
      "--no-sandbox",
      `--user-data-dir=${userDataDir}`
    ],
    dumpio: true
  });
  console.log("Brave launched!");
  const page = await browser.newPage();
  await page.goto("https://google.com");
  console.log("Google loaded!");
  // await browser.close();
})();
