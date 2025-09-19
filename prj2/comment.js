// Import necessary libraries
const fs = require('fs');
const csv = require('csv-parser');
const puppeteer = require('puppeteer');

const CSV_FILE_PATH = './Hemkoop_links/meat/hemkop_meat.csv';
const OUTPUT_FILE_PATH = 'scraped_data.json';

/**
 * Reads URLs from a specified CSV file.
 * @param {string} filePath - The path to the CSV file.
 * @returns {Promise<string[]>} A promise that resolves to an array of URLs.
 */
function getUrlsFromCsv(filePath) {
  return new Promise((resolve, reject) => {
    const urls = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => {
        if (row.url) {
          urls.push(row.url);
        }
      })
      .on('end', () => {
        console.log(`CSV processed. Found ${urls.length} links.`);
        resolve(urls);
      })
      .on('error', reject);
  });
}

/**
 * Main function to orchestrate the scraping process.
 */
async function runScraper() {
  const urls = await getUrlsFromCsv(CSV_FILE_PATH);
  const scrapedData = [];

  console.log("Launching browser...");
  const browser = await puppeteer.launch({ headless: false });

  console.log("Starting to scrape pages...");
  for (const url of urls) {
    let page;
    try {
      page = await browser.newPage();
        page.on('console', msg => {
    console.log('PAGE LOG:', msg.text());
  });

      await page.goto(url, { waitUntil: 'networkidle2' });
      // Handle the cookie consent banner
try {
  // Use the class from the parent <a> tag
  const cookieButtonSelector = '#onetrust-accept-btn-handler'; 
  await page.waitForSelector(cookieButtonSelector, { timeout: 5000 });
  await page.click(cookieButtonSelector);
  console.log("✅ Cookie consent banner accepted.");
} catch (error) {
  console.log("ℹ️ Cookie consent banner not found or already accepted.");
}
      
      // --- B. SCRAPE THE PRODUCT DATA ---
      const productTitle = await page.$eval('h1', h1 => h1.textContent.trim());
      const productDescription= await page.$eval('.caySWU', p=>p.innerText);
  const price = await page.$eval(
    'span[data-testid="price-container"]',
    el => el.innerText
  );

  console.log("Price:", price);
      // Step 1: Click the correct <button> to reveal the nutrition content// 1. Click Näringsvärde tab
    await page.click('.hRlDxS');


// 2. Scroll a bit to trigger lazy rendering
await page.evaluate(() => window.scrollBy(0, 1500));
await new Promise(r => setTimeout(r, 10000))


      const nutritionData = await page.$$eval(`tbody tr`, rows => {
        const data = {};
        console.log("object")
        rows.forEach(row => {
          if (row.cells[0] && row.cells[1]) {
            const key = row.cells[0].textContent.trim();
            const value = row.cells[1].textContent.trim();
            data[key] = value;
          }
        });
        return data;
      });


      
      // --- C. STORE AND LOG THE RESULTS ---
      scrapedData.push({
        title: productTitle,
        price: price,
        product_description: productDescription,
        url: url,
        nutrition: nutritionData
      });

      console.log(`✅ Successfully scraped: ${productTitle}`);
console.log('The following data was scrapped:', JSON.stringify(nutritionData, null, 2));
    } catch (error) {
      console.error(`❌ Failed to scrape ${url}: ${error.message}`);
    } 

     // --- 5. SAVE THE RESULTS ---
    if (Object.keys(scrapedData).length > 0) {
      fs.writeFileSync(OUTPUT_FILE_PATH, JSON.stringify(scrapedData, null, 2));
      console.log(`\nResults saved to ${OUTPUT_FILE_PATH}`);
      console.log(scrapedData);
    } else {
      console.log("\nNo data was scraped.");
    }
    
  }
 

  // 6. Close the browser and save the final results
  await browser.close();
  console.log("\nProcess complete!");

    
  }


// Run the script and handle any top-level errors
runScraper().catch(error => console.error("An unexpected error occurred:", error));