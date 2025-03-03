const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  try {
    // Connect to existing Brave instance
    const browser = await puppeteer.connect({
      browserWSEndpoint: 'ws://127.0.0.1:9222/devtools/browser/cd7f9e82-7c27-42f6-875d-20ab0447d581',
    });
    console.log('Connected successfully!');

    // Open a new page
    const page = await browser.newPage();
    console.log('Navigating to Grok chat...');
    await page.goto('https://example.com/grok-chat', { waitUntil: 'domcontentloaded', timeout: 30000 }); // Replace URL as needed

    // Save the page content
    console.log('Saving page content...');
    const html = await page.content();
    fs.writeFileSync('/Users/ian/dev/projects/agents/local/grok/repo/local/html/grok_chat.html', html);
    console.log('HTML saved');

    // Disconnect from Brave but don't close it
    await browser.disconnect();
    console.log('Disconnected from Brave, leaving it running');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1); // Exit with error code if something fails
  }
  // Exit cleanly
  process.exit(0);
})();
