// Import the Puppeteer library
const fs = require('fs');
const puppeteer = require('puppeteer');

// --- 1. CONFIGURE YOUR SCRAPER ---
// Paste the full URL you want to start with here
const START_URL = 'https://www.coop.se/handla/varor/kott-fagel-chark/korv/falukorv/falukorv-7300156578624';
const OUTPUT_FILE_PATH = 'coop_scraped_data.json';


/**
 * The main function to run the scraper.
 */
async function scrapeCoopProduct() {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({ headless: false,slowMo:10 }); // Use headless: false to see the browser in action
  const page = await browser.newPage();
  
  let scrapedData = {};

  try {
    // --- 2. NAVIGATE AND PREPARE THE PAGE ---
    console.log(`Navigating to: ${START_URL}`);
    await page.goto(START_URL, { waitUntil: 'networkidle2' });

try {
  // Use the class from the parent <a> tag
 
  await page.click('.cmptxt_btn_yes');
  console.log("✅ Cookie consent banner accepted.");
} catch (error) {
  console.log("ℹ️ Cookie consent banner not found or already accepted.");
}
   

    // --- 3. PERFORM ACTIONS (e.g., CLICK A BUTTON) ---
    // **ACTION REQUIRED**: Replace this with the selector for the button you need to click.
    // Use the "Inspect Element" tool in your browser to find a stable ID or class.
const revealButtonSelector = "//button[.//h2[contains(text(), 'Näringsinnehåll')]]";   
//  console.log(`Waiting for reveal button: ${revealButtonSelector}`);
   console.log(`Waiting for reveal button using XPath...`);

// Use the 'xpath/' prefix to tell Puppeteer this is an XPath selector
await page.waitForSelector('xpath/' + revealButtonSelector);
await page.click('xpath/' + revealButtonSelector);

console.log("✅ Clicked the 'Näringsinnehåll' button.");
    
    // --- 4. SCRAPE THE DATA ---
    // **ACTION REQUIRED**: This uses the class you provided.
    // WARNING: '.pjP0dWJX' looks like an auto-generated class and might break easily.
    // Try to find a more stable, descriptive selector if possible.
    const dataSelector = '.pjP0dWJX';
    console.log(`Waiting for data elements: ${dataSelector}`);
    await page.waitForSelector(dataSelector); // Wait for the data to be visible after the click

    // This finds all elements with your class and extracts their text
    const extractedTexts = await page.$$eval(dataSelector, elements => {
      // This code runs in the browser
      // It maps over each found element and returns its visible text
      return elements.map(el => el.innerText.trim());
    });

    scrapedData = {
      url: START_URL,
      data: extractedTexts,
    };
    
    console.log("✅ Data scraped successfully!");

  } catch (error) {
    console.error(`❌ An error occurred: ${error.message}`);
  } finally {
    // --- 5. CLEAN UP ---
    await browser.close();
    console.log("\nBrowser closed.");
  }

  // --- 6. SAVE THE RESULTS ---
  if (Object.keys(scrapedData).length > 0) {
    fs.writeFileSync(OUTPUT_FILE_PATH, JSON.stringify(scrapedData, null, 2));
    console.log(`\nResults saved to ${OUTPUT_FILE_PATH}`);
    console.log(scrapedData);
  } else {
    console.log("\nNo data was scraped.");
  }
}

// Run the scraper
scrapeCoopProduct();