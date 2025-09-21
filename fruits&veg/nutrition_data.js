// hemkop_links.js
const fs = require("fs");
const puppeteer = require("puppeteer");

const START_URL = "https://www.hemkop.se/sortiment/frukt-och-gront";
const OUT = "hemkop_fruit_veg_links.csv";

async function autoScroll(page) {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let totalHeight = 0;
      const distance = 400;
      const timer = setInterval(() => {
        window.scrollBy(0, distance);
        totalHeight += distance;
        if (totalHeight >= document.body.scrollHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 150);
    });
  });
}

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  try {
    await page.goto(START_URL, { waitUntil: "networkidle2", timeout: 60000 });

    try {
      await page.waitForSelector("#onetrust-accept-btn-handler", { timeout: 4000 });
      await page.click("#onetrust-accept-btn-handler");
    } catch {}

    await autoScroll(page);
    await new Promise((r) => setTimeout(r, 1200));

    const selector = 'a[data-testid="link-area"]';
    await page.waitForSelector(selector, { timeout: 20000 });

    const links = await page.$$eval(selector, els =>
      [...new Set(els.map(a => a.href))]
    );

    fs.writeFileSync(OUT, "url\n" + links.join("\n"), "utf8");
    console.log(`✅ Saved ${links.length} links to ${OUT}`);
  } catch (err) {
    console.error("Error:", err.message);
  } finally {
    await browser.close();
  }
})();
