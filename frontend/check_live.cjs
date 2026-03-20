const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    
    // Capture console messages
    page.on('pageerror', err => {
        console.log('PAGE ERROR:', err.toString());
    });
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('CONSOLE ERROR:', msg.text());
        }
    });

    try {
        await page.goto('https://careerdna-frontend.onrender.com', { waitUntil: 'networkidle0' });
        const html = await page.content();
        if (html.length < 500) {
            console.log("HTML TOO SHORT:", html);
        } else {
            console.log("PAGE RENDERED SUCCESSFULLY.");
        }
    } catch (e) {
        console.log('NAVIGATION ERROR:', e.message);
    }
    await browser.close();
})();
