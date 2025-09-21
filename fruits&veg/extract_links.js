const fs = require("fs");
const { parse } = require("json2csv");
const puppeteer = require("puppeteer");

const LINKS_FILE = "hemkop_fruit_veg_links.csv";
const OUT = "hemkop_fruit_veg_full.csv";

// 1️⃣ List of nutrients you want as columns
const NUTRIENTS = [
  "Energi (kcal)",
  "Energi (kJ)",
  "Fett",
  "Varav mättat fett",
  "Kolhydrat",
  "Varav sockerarter",
  "Protein",
  "Salt",
  "Fiber",
  "Varav polyoler",
  "Fosfor",
  "Vitamin B12",
  "Vitamin D",
  "Folsyra",
  "Selen",
  "Järn",
  "Magnesium",
  "Zink",
  "Varav enkelomättat fett",
  "Varav fleromättat fett",
  "Fluorid",
  "Vitamin B6",
  "Natrium",
  "Kalcium",
  "Material",
  "Kalium",
  "Vitamin E",
  "Pantotensyra",
];

async function readLinks() {
  return fs
    .readFileSync(LINKS_FILE, "utf8")
    .split("\n")
    .slice(1)
    .map((l) => l.trim())
    .filter(Boolean);
}

async function getProductData(page, url) {
  await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
  await page.waitForSelector("h1", { timeout: 30000 });

  const result = await page.evaluate(() => {
    const name = document.querySelector("h1")?.textContent.trim() || "";

    const price =
      document.querySelector('[data-testid="price"]')?.textContent.trim() ||
      document.querySelector('[class^="Price_"]')?.textContent.trim() ||
      "";

    const size =
      document.querySelector('[data-testid="product-size"]')?.textContent.trim() ||
      "";

    const nutrition = {};
    const rows = document.querySelectorAll('[data-testid="nutrient-table"] tr');
    rows.forEach((tr) => {
      const cells = tr.querySelectorAll("td, th");
      if (cells.length >= 2) {
        const key = cells[0].textContent.trim();
        const val = cells[1].textContent.trim();
        nutrition[key] = val;
      }
    });

    return { name, price, size, nutrition };
  });

  return { url, ...result };
}

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  const urls = await readLinks();
  const results = [];

  for (let i = 0; i < urls.length; i++) {
    try {
      const data = await getProductData(page, urls[i]);
      results.push(data);
      console.log(`(${i + 1}/${urls.length}) scraped: ${data.name}`);
      await new Promise((r) => setTimeout(r, 300));
    } catch (err) {
      console.error(`Error with ${urls[i]}:`, err.message);
    }
  }

  await browser.close();

  // 2️⃣ Flatten and ensure all nutrients exist (null if missing)
  const flat = results.map((r) => {
    const base = { url: r.url, name: r.name, price: r.price, size: r.size };
    NUTRIENTS.forEach((nut) => {
      base[nut] = r.nutrition[nut] ?? null;
    });
    return base;
  });

  // 3️⃣ Export to CSV
  const fields = ["url", "name", "price", "size", ...NUTRIENTS];
  const csv = parse(flat, { fields, defaultValue: null });

  fs.writeFileSync(OUT, csv, "utf8");
  console.log(`✅ Saved ${flat.length} products to ${OUT}`);
})();
