// Run with Playwright on NODE_PATH or installed locally. The server URL is optional.
const {chromium} = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const root = process.argv[2] || "http://127.0.0.1:8713/";
const audit = [];
async function main(){
  const options = {headless:true};
  if(process.env.EDITION_BROWSER)options.executablePath=process.env.EDITION_BROWSER;
  const browser=await chromium.launch(options);
  try {
    for(const [name,width,height] of [["desktop",1366,900],["mobile",390,844],["narrow",320,640]]) {
      const page=await browser.newPage({viewport:{width,height},isMobile:width<=390,hasTouch:width<=390});
      const errors=[];
      page.on("pageerror",error=>errors.push(error.message));
      page.on("response",response=>{if(response.status()>=400)errors.push(response.url()+" "+response.status())});
      await page.goto(root);await page.evaluate(()=>document.fonts.ready);
      assert.equal(await page.locator("h1").innerText(),"Deciphering\nHYBRID");
      if(process.env.EDITION_SCREENSHOTS){fs.mkdirSync(process.env.EDITION_SCREENSHOTS,{recursive:true});await page.screenshot({path:process.env.EDITION_SCREENSHOTS+"/"+name+".png"});}
      await page.getByRole("link",{name:"Read the quickstart"}).click();
      await page.locator("header.mast summary").click();
      await page.locator("header.mast details nav").getByRole("link",{name:"Rule catalogue"}).click();
      await page.waitForLoadState("load");
      await page.waitForFunction(()=>document.getElementById("matches").textContent.startsWith("Showing "));
      const form=page.locator(".filters"), number=form.locator("[name=number]");
      const before=await page.locator("[data-row]").count();
      assert.equal(await page.locator("#matches").textContent(),"Showing "+before+" of "+before+" segments.");
      await number.fill("188");
      const after=await page.locator("[data-row]:visible").count();
      assert(after>=2 && after<before);
      const first=page.locator("[data-row]:visible").first();
      for(const key of ["topic","relevance","confidence","status","edition"]) {
        const value=(await first.getAttribute("data-"+key)).split("|")[0];
        await form.locator('[name="'+key+'"]').selectOption(value);
      }
      assert(await page.locator("[data-row]:visible").count()>=1);
      await form.locator("[name=q]").fill("unmatched-qzv");
      assert.equal(await page.locator("[data-row]:visible").count(),0);
      await form.getByRole("button",{name:"Reset"}).click();
      await page.waitForFunction(()=>document.querySelectorAll("[data-row][hidden]").length===0);
      await page.goto(root+"glossary.html#dp");
      await page.locator(".filters input[name=q]").fill("psyche");
      assert(await page.locator("#dp").isVisible());
      await page.goto(root+"search.html?q=camouflage");
      assert(await page.locator("#search-results a").count()>0);
      await page.goto(root+"architecture.html");
      await page.locator("#node").selectOption("rule-45");
      assert(await page.locator("#neighbours a").count()>0);
      const overflow=[];
      for(const dest of ["index","quickstart","catalogue","glossary","mathematics","architecture","playability","assessment","sources","book-combat"]) {
        await page.goto(root+dest+".html");await page.evaluate(()=>document.fonts.ready);
        if(await page.evaluate(w=>document.documentElement.scrollWidth>w+1,width))overflow.push(dest);
      }
      assert.deepEqual(overflow,[]);assert.deepEqual(errors,[]);
      audit.push({viewport:name,width,height,segments_before_rule_filter:before,segments_after_rule_188:after,overflow,errors});
      await page.close();
    }
  } finally {await browser.close();}
  console.log(JSON.stringify(audit,null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1});
