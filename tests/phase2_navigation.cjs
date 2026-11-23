// Run alongside tests/browser.cjs, with the same browser and environment variables.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {chromium} = require("playwright");
const root = process.argv[2] || "http://127.0.0.1:8713/";
const destinations = ["handbook", "sheets", "characters", "builder", "playground",
  "atlas", "session", "configurations", "adaptation", "replay", "reference"];

async function checkViewport(browser, width) {
  const page = await browser.newPage({viewport:{width,height:900},isMobile:width < 600, hasTouch:width < 600});
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("response", response => {if (response.status() >= 400) errors.push(response.url());});
  await page.goto(root);
  await page.getByRole("link",{name:"Read the handbook",exact:true}).click();
  await page.getByRole("heading",{name:"HYBRID in Plain English",exact:true,level:1}).waitFor();
  await page.locator(".handbook details").first().locator("summary").click();
  assert(await page.locator(".handbook details[open]").count() === 1);
  for (const slug of destinations) {
    await page.goto(root+slug+".html");
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator("h1").count(), 1, slug);
    const measured=await page.evaluate(()=>document.documentElement.scrollWidth);
    assert(measured <= width+1, slug+" overflow at "+width+"px (content width "+measured+")");
    if (process.env.EDITION_SCREENSHOTS && ["builder","session","handbook"].includes(slug)) {
      fs.mkdirSync(process.env.EDITION_SCREENSHOTS,{recursive:true});
      await page.screenshot({path:path.join(process.env.EDITION_SCREENSHOTS,slug+"-"+width+".png")});
    }
  }
  await page.goto(root+"search.html?q=Lantern");
  await page.locator("#search-results a[href^='session.html']").first().waitFor();
  await page.goto(root+"handbook.html#scales");
  assert.equal(await page.locator("#scales table tbody tr").count(),3);
  await page.goto(root+"atlas.html");
  const allRows = await page.locator("[data-row]").count();
  assert.equal(allRows,205);
  await page.locator("select[name=kind]").selectOption({label:"False positive"});
  const retained = await page.locator("[data-row]:visible").count();
  assert.equal(retained,4);
  await page.locator("form.filters button[type=reset]").click();
  await page.waitForFunction(()=>document.querySelectorAll("[data-row][hidden]").length===0);
  assert.deepEqual(errors,[]);
  await page.close();
  return {viewport:width,pages_checked:destinations.length,atlas_rows_before:allRows,atlas_rows_after:retained,script_or_asset_errors:errors};
}

(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.EDITION_BROWSER || undefined});
  try {
    const results=await Promise.all([1366,390,320].map(w=>checkViewport(browser,w)));
    console.log(JSON.stringify(results,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
