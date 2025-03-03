const puppeteer = require("puppeteer");

(async () => {
  const bravePath = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
  const browser = await puppeteer.launch({
    executablePath: bravePath,
    headless: false
  });
  const page = await browser.newPage();
  await page.goto("https://google.com");
  console.log("Brave opened!");
  // await browser.close();
})();
