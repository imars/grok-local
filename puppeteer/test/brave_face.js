const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const args = process.argv.slice(2);
const shouldCloseBrowser = args.includes('--test');
const actionIndex = args.findIndex(arg => arg.startsWith('--action='));
const actionArg = actionIndex !== -1 ? args[actionIndex] : '--action=connect';
const action = actionArg.slice(9);
const usernameIndex = args.indexOf('--username');
const passwordIndex = args.indexOf('--password');
const verifyIndex = args.indexOf('--verify');
const username = usernameIndex !== -1 ? args[usernameIndex + 1] : null;
const password = passwordIndex !== -1 ? args[passwordIndex + 1] : null;
const verify = verifyIndex !== -1 ? args[verifyIndex + 1] : null;

async function braveInterface() {
    console.log("Starting Brave Interface Script");
    console.log(`Action: ${action}`);
    console.log(`Close browser: ${shouldCloseBrowser ? 'yes' : 'no'}`);

    let browser;

    try {
        console.log("Attempting to connect to existing Brave instance...");
        browser = await puppeteer.connect({
            browserURL: 'http://localhost:9222',
            defaultViewport: null
        });
        console.log("✓ Connected to existing Brave instance");

        let pages = await browser.pages();
        let page = pages.find(p => p.url().includes('x.com/i/grok?conversation=1895083745784254635')) || pages[0];

        console.log("Current open tabs:");
        for (const p of pages) {
            console.log(`URL: ${p.url()}`);
        }

        if (action === 'connect') {
            const currentUrl = page.url();
            const isLoggedIn = currentUrl.includes('x.com') && !currentUrl.includes('login');
            
            if (!isLoggedIn) {
                console.log("Navigating to X messages...");
                await page.goto('https://x.com/messages', { waitUntil: 'networkidle2' });
                console.log(`Current URL after navigation: ${page.url()}`);

                if (page.url().includes('login')) {
                    if (!username) {
                        console.log("✗ Login required but missing username.");
                    } else {
                        console.log("Login page detected, autofilling username...");
                        await page.waitForSelector('input[name="text"]', { timeout: 10000 });
                        console.log("Typing username...");
                        await page.type('input[name="text"]', username);
                        console.log("Username entered. Pausing for manual login...");
                        console.log("Please verify username, enter password, and press Login manually.");
                        console.log("After login, Ctrl+C to exit or let Brave run.");
                        await new Promise(() => {}); // Pause indefinitely
                    }
                } else {
                    console.log("✓ Successfully navigated to X messages");
                }
            } else {
                console.log("✓ Already logged in to X");
            }
        } else if (action.startsWith('open-tab=')) {
            const url = action.substring(9);
            console.log(`Opening tab: ${url}...`);
            const newPage = await browser.newPage();
            await newPage.goto(url, { waitUntil: 'networkidle2' });
            console.log(`✓ Opened tab: ${newPage.url()}`);
        } else if (action.startsWith('read-chat=')) {
            const url = action.substring(10);
            console.log(`Reading chat messages from existing tab: ${url}...`);
            console.log(`Current URL: ${page.url()}`);
            const isLoggedIn = !page.url().includes('login') && page.url().includes('x.com');
            if (!isLoggedIn) {
                console.log("✗ Not logged in or wrong tab. Please ensure the test channel tab is open and logged in manually.");
                return;
            }
            await page.bringToFront();
            await page.waitForSelector('body', { timeout: 15000 });
            const messages = await page.evaluate(() => {
                const messageElements = document.querySelectorAll('div[data-testid="tweetText"]');
                if (messageElements.length === 0) {
                    return { messages: [], html: document.body.innerHTML.slice(0, 1000) };
                }
                return { messages: Array.from(messageElements).map(el => el.innerText), html: null };
            });
            console.log("Chat messages:");
            if (messages.messages.length > 0) {
                messages.messages.forEach((msg, index) => console.log(`[${index}]: ${msg}`));
            } else {
                console.log("No messages found. Dumping partial HTML for debugging:");
                console.log(messages.html);
                console.log("If this is an error page, please manually refresh the tab and ensure it’s logged in.");
            }
        } else if (action.startsWith('send-message=')) {
            const message = action.substring(13);
            console.log(`Sending message to test channel: ${message}...`);
            if (!page.url().includes('x.com/i/grok?conversation=1895083745784254635')) {
                console.log("Tab not active, navigating...");
                await page.goto('https://x.com/i/grok?conversation=1895083745784254635', { waitUntil: 'networkidle2' });
            }
            console.log(`Current URL: ${page.url()}`);
            const isLoggedIn = !page.url().includes('login') && page.url().includes('x.com');
            if (!isLoggedIn) {
                console.log("✗ Not logged in. Please ensure the test channel tab is logged in manually.");
                return;
            }
            await page.bringToFront();
            await page.waitForSelector('div[role="textbox"]', { timeout: 15000 });
            await page.type('div[role="textbox"]', message);
            await page.keyboard.press('Enter');
            console.log("✓ Message sent successfully.");
        } else {
            console.log(`✗ Unknown action: ${action}`);
        }

    } catch (e) {
        console.log(`✗ Error: ${e.message}`);
        console.log("Please ensure Brave is running with --remote-debugging-port=9222.");
        process.exit(1);
    } finally {
        if (browser) {
            console.log("\nDisconnecting from browser...");
            await browser.disconnect();
            console.log("✓ Disconnected successfully");
        }
    }
}

braveInterface();