// Pass --numeric for the offline equation and character replay only.
const assert = require("node:assert/strict");
const operations = require("../web/phase2-tools.js");
const cases = require("../data/phase2/worked_characters.json");

function close(a,b,tol=1e-10) {
  assert(Number.isFinite(a) && Math.abs(a-b) <= tol * Math.max(1, Math.abs(b)), a+" versus "+b);
}

function numericReplay() {
  let matched=0, numericFields=0;
  const ids=cases.map(c=>c.id);
  assert.equal(new Set(ids).size,5);
  for(const c of cases){
    const replay=operations.build(c.inputs);
    assert.deepEqual(replay.errors,[],c.id);
    for(const [key,expected] of Object.entries(c.expected)){
      if(expected === null)assert.equal(replay.values[key],undefined);
      else {close(replay.values[key],expected);numericFields++;}
    }
    matched++;
  }
  for(const [from,to,init,out] of [["CA","C3",10,10],["C1","C3",20,733.0985575968451],
    ["C2","C3",0.1,10],["C4","CA",1,1],["C0","C0",7,7]]){
    close(operations.convert(init,from,to),out);
  }
  const far=operations.convert(20,"CA","C3");
  close(operations.convert(far,"C3","CA","high"),20);
  close(operations.convert(far,"C3","CA","low"),0.05);
  for(const [value,from,to,branch] of [["","C2","C3",""],[0,"C2","C3",""],
    [10,"C0","C1",""],[0.2,"C2","C1","high"],[35,"C3","C2",""],[1e200,"C1","C4",""]]){
    assert.throws(()=>operations.convert(value,from,to,branch));
  }
  assert.deepEqual(operations.split(40,"add",20),{pl:60,ls:20});
  assert.deepEqual(operations.split(40,"multiply",2),{pl:80,ls:20});
  assert.deepEqual(operations.split(40,"add",-10),{pl:30,ls:50});
  assert.throws(()=>operations.split(10,"add",10));
  assert.throws(()=>operations.split(10,"multiply",0));
  assert.throws(()=>operations.pool("6,,6",6));assert.throws(()=>operations.pool("6.1",6));
  assert.throws(()=>operations.pool("21",20));assert.equal(operations.pool("6, 6, 6",6),18);
  assert.throws(()=>operations.advantage(9,["General telepathy"]));
  assert.equal(operations.advantage(9,["Agility","Minor force field","Minor telepathy to control insects","Shape-shifting"]).dp,45);
  assert.deepEqual(operations.highRoll(3,"66"),{threshold:12,total:"216",pass:"81",probability:.375});
  assert.equal(operations.highRoll(25,"66").threshold,99);
  assert.equal(operations.highRoll(25,"two-thirds").threshold,100);
  assert.throws(()=>operations.highRoll(3.5,"66"));
  assert.equal(operations.runDemo("roll",{law:"under",c3:35,baseline:10,branch:"high"}).result,"7 or less");
  assert.equal(operations.runDemo("damage",{law:"mutant",rating:30}).result,"9d6");
  assert.equal(operations.runDemo("damage",{law:"subtract",rating:49}).result,"6d6");
  assert.equal(operations.runDemo("damage",{law:"root",rating:49}).result,"7d6");
  assert.match(operations.runDemo("damage",{law:"root",rating:50}).result,/fractional/);
  assert.equal(operations.runDemo("speed",{law:"running",dp:20}).result,"10 mph");
  assert.match(operations.runDemo("speed",{law:"mutant",dp:20}).result,/49\.2809/);
  assert.match(operations.runDemo("advantages",{count:3}).result,/36 C2 DP/);
  const blank=operations.build({...cases[0].inputs,rating:""});
  assert(!blank.values.dp && blank.errors.length===1);
  const uncertain=operations.build({...cases[0].inputs,defaultPair:false,power:"cloak",cloakSource:""});
  assert(!("ls" in uncertain.values) && !("phasing" in uncertain.values));
  const openCom=operations.build({...cases[0].inputs,defaultPair:false,com:5});
  assert.equal(openCom.rows.find(r=>r.key==="com").value,"5 C2 COM");
  assert.equal(openCom.rows.find(r=>r.key==="remainder").value,"Unresolved");
  assert.equal(operations.build({...cases[2].inputs,gifts:[]}).rows.find(r=>r.key==="stage").value,"Intermediate state");
  const unsupported=operations.build({...cases[0].inputs,power:"phase"});
  assert.match(unsupported.rows.find(r=>r.key==="capability").value,/Outside/);
  assert.match(operations.build({...cases[0].inputs,power:"camouflage"}).rows.find(r=>r.key==="capability").value,/unresolved/);
  const clairvoyant={...cases[0].inputs,scale:"C1",power:"time-sight"};
  for (const [rating,expected] of [[30,"disputed 30 C1"],[40,"40 C1 example"],[50,"No matching case"]]){
    assert(operations.build({...clairvoyant,rating}).rows.find(r=>r.key==="capability").value.includes(expected));
  }
  assert.deepEqual(operations.build({...cases[0].inputs,com:17}).errors.length,1);
  console.log("Character replay: "+cases.length+" fixture rows before, "+matched+" matched after. "+
    numericFields+" independent numerical expectations. Zero unmatched or duplicate character IDs.");
}

async function browserReplay(base) {
  const {chromium}=require("playwright");
  const options={headless:true};
  if(process.env.EDITION_BROWSER)options.executablePath=process.env.EDITION_BROWSER;
  const browser=await chromium.launch(options);
  try {
    for(const [width,height] of [[1366,900],[390,844],[320,640]]) {
      const page=await browser.newPage({viewport:{width,height},isMobile:width<480,hasTouch:width<480});
      const errors=[];
      page.on("pageerror",err=>errors.push(err.message));
      page.on("response",r=>{if(r.status()>=400)errors.push(r.status()+" "+r.url());});
      for(const slug of ["sheets","characters","builder","playground"]) {
        await page.goto(base+slug+".html");
        await page.evaluate(()=>document.fonts.ready);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),slug+" overflow at "+width);
      }
      const demo=(name)=>page.locator('[data-demo="'+name+'"]');
      const form=page.locator("#character-builder");
      await demo("scale").locator('[name="from"]').selectOption("C3");
      await demo("scale").locator('[name="to"]').selectOption("C1");
      await demo("scale").locator('[name="rating"]').fill("733.0985575968451");
      assert.match(await demo("scale").locator("output").innerText(),/Select an inverse branch/);
      await demo("scale").locator('[name="branch"]').selectOption("low");
      assert.match(await demo("scale").locator("output strong").innerText(),/0\.05 C1/);
      await demo("scale").locator('[name="branch"]').selectOption("high");
      assert.equal(await demo("scale").locator("output strong").innerText(),"20 C1");
      await demo("roll").locator('[name="law"]').selectOption("under");
      assert.equal(await demo("roll").locator("output strong").innerText(),"7 or less");
      await demo("damage").locator('[name="rating"]').fill("50");
      assert.match(await demo("damage").locator("output strong").innerText(),/fractional/);
      await demo("trade").locator('[name="operation"]').selectOption("add");
      await demo("trade").locator('[name="amount"]').fill("20");
      assert.match(await demo("trade").locator("output strong").innerText(),/^60 C2 PL/);
      await demo("trade").locator('button').click();
      await page.waitForFunction(()=>document.querySelector('[data-demo="trade"] output strong').textContent.startsWith("80 C2 PL"));
      for(const c of cases) {
        await page.goto(base+"builder.html?character="+c.id);
        assert.equal(await page.locator("#built-sheet h2").innerText(),c.inputs.name);
        assert.equal(await form.locator('[name="concept"]').inputValue(),c.concept);
        assert.equal(await page.locator('#built-sheet [data-key="dp"]').innerText(),operations.fmt(c.expected.dp)+" C2 DP");
        assert.equal(await page.locator('#built-sheet .tool-error').count(),0);
      }
      await form.locator('[name="route"]').selectOption("benchmark");
      await form.locator('[name="scale"]').selectOption("C1");
      await form.locator('[name="rating"]').fill("30");
      assert.match(await page.locator('[data-key="capability"]').innerText(),/disputed 30 C1/);
      await form.locator('[name="rating"]').fill("50");
      assert.match(await page.locator('[data-key="capability"]').innerText(),/No matching case/);
      await page.locator("#clear-builder").click();
      assert.equal(await form.locator('[name="rating"]').inputValue(),"");
      assert.match(await page.locator("#built-sheet").innerText(),/Enter a starting Psyche/);
      await form.locator('[name="name"]').fill("Morgan <example>");
      await form.locator('[name="age"]').fill("28");
      await form.locator('[name="concept"]').fill("Lighthouse keeper");
      await form.locator('[name="limitation"]').fill("Needs a quiet minute");
      await form.locator('[name="rating"]').fill("16");
      await form.locator('[name="scale"]').selectOption("C0");
      assert.match(await page.locator("#built-sheet").innerText(),/no universal neighbour/);
      await form.locator('[name="scale"]').selectOption("C2");
      await form.locator('[name="power"]').selectOption("cloak");
      assert.match(await page.locator("#built-sheet").innerText(),/unspecified total/);
      await form.locator('[name="defaultPair"]').check();
      await form.locator('[name="cloakSource"]').selectOption("pl");
      assert.equal(await page.locator('[data-key="phasing"]').innerText(),"2.08%");
      await form.locator('[name="com"]').fill("6");
      assert.equal(await page.locator('[data-key="remainder"]').innerText(),"10 C2");
      await page.evaluate(()=>{window.print=()=>{document.body.dataset.printed=document.querySelector(".print-target").id;};});
      await page.locator('[data-print="built-sheet"]').click();
      await page.emulateMedia({media:"print"});
      assert.equal(await page.locator("body").getAttribute("data-printed"),"built-sheet");
      assert(!(await form.isVisible()));
      const printed=await page.locator("#built-sheet").innerText();
      for(const val of ["Morgan <example>","Age 28","Lighthouse keeper","Needs a quiet minute","10 C2","2.08%"])assert(printed.includes(val),val);
      const pdf=await page.pdf({format:"A4",preferCSSPageSize:true});
      assert(pdf.length>2000);
      await page.evaluate(()=>dispatchEvent(new Event("afterprint")));
      await page.emulateMedia({media:"screen"});
      assert(await form.isVisible());
      await page.goto(base+"sheets.html");
      for(const which of ["minimal-blank","full-blank","minimal-ordinary-courier","full-ordinary-courier"]){
        assert.equal(await page.locator('[data-print="'+which+'"]').count(),1);
      }
      await page.evaluate(()=>{window.print=()=>{};});
      await page.locator('[data-print="full-blank"]').click();
      await page.emulateMedia({media:"print"});
      assert(await page.locator("#full-blank").isVisible());
      assert(!(await page.locator("#minimal-blank").isVisible()));
      assert((await page.pdf({format:"A4",preferCSSPageSize:true})).length>2000);
      assert.deepEqual(errors,[]);
      await page.close();
      console.log("Browser "+width+"×"+height+": 4 pages, 5 character replays, inverse branches, unresolved inputs, reset, sheet/PDF output, no overflow or browser errors.");
    }
  } finally {await browser.close();}
}

numericReplay();
if(!process.argv.includes("--numeric")){
  const base=(process.argv[2]||"http://127.0.0.1:8713/").replace(/\/?$/,"/");
  browserReplay(base).catch(e=>{console.error(e);process.exitCode=1;});
}
