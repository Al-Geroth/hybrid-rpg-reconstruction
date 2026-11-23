/* Numerical operations used by the four static Learn and Play pages. */
(() => {
  "use strict";
  const classes = ["CA", "C1", "C2", "C3", "C4"];
  const gifts = [
    ["Agility", "Increased height", "Martial arts"],
    ["Minor force field", "Agility", "Increased height", "Martial arts", "Minor resistance to toxins"],
    ["Camouflage", "Force field", "Minor shape-shifting", "Minor healing factor", "Minor energy projection", "Minor telepathy to control insects"],
    ["Shape-shifting"]
  ];
  const powerNames = {none: "No individual effect specified", running: "Running",
    camouflage: "Camouflage", phase: "Desolidification", "time-sight": "Two-direction time perception",
    cloak: "Phasing or cloaking percentage"};
  const fmt = n => !Number.isFinite(n) ? "Unresolved" :
    (Math.abs(n) >= 1e8 || (n !== 0 && Math.abs(n) < 0.0001))
      ? n.toExponential(5) : Number(n.toPrecision(8)).toLocaleString("en-US", {maximumFractionDigits: 8});
  const fail = message => { throw new Error(message); };
  function numeric(value, label, positive = false) {
    if (value == null || String(value).trim() === "") fail("Enter " + label + ".");
    const n = Number(value);
    if (!Number.isFinite(n)) fail("Use a finite number for " + label + ".");
    if (positive && n <= 0) fail(label + " must be greater than zero.");
    return n;
  }
  function finite(n) {
    if (!Number.isFinite(n) || n === 0) fail("The result exceeds the nonzero numerical range of this calculator.");
    return n;
  }
  function convert(value, from, to, branch = "") {
    const x = numeric(value, "the scale rating", true);
    if (from === "C0" || to === "C0") {
      if (from === "C0" && to === "C0") return x;
      fail("C0 needs a statistic and a local conversion such as rule 5. It has no universal neighbour in the chain.");
    }
    if (!classes.includes(from) || !classes.includes(to)) fail("Choose two named class scales.");
    const steps = classes.indexOf(to) - classes.indexOf(from);
    if (!steps) return x;
    const u = Math.log10(x);
    if (steps > 0) return finite(10 ** (u ** (2 ** steps)));
    if (u < 0) fail("There is no real inverse of a class value below one.");
    if (u === 0) return 1;
    if (branch !== "high" && branch !== "low") fail("Select an inverse branch. Both a rating above one and its reciprocal encode this output.");
    return finite(10 ** ((branch === "high" ? 1 : -1) * u ** (2 ** steps)));
  }
  function split(dp, mode, amount) {
    dp=numeric(dp, "the baseline", true);
    if (mode === "none") return {pl: dp, ls: dp};
    if (mode !== "add" && mode !== "multiply") fail("Choose a trade operation.");
    const a = numeric(amount, mode === "add" ? "the signed point adjustment" : "the factor", mode === "multiply");
    const pl = mode === "add" ? dp + a : dp * a;
    const ls = mode === "add" ? dp - a : dp / a;
    if (pl <= 0 || ls <= 0) fail("This trade leaves a nonpositive PL or LS. Positive ratings are needed for the downstream class calculation.");
    return {pl: finite(pl), ls: finite(ls)};
  }
  function pool(faces, sides) {
    const max = numeric(sides, "the number of sides", true);
    if (!Number.isSafeInteger(max) || max < 2) fail("A die needs a whole number of at least two sides.");
    const parts = String(faces || "").split(",");
    if (parts.length > 100) fail("This reader supports at most 100 entered faces.");
    const numbers = parts.map(v => numeric(v, "each die face", true));
    if (!numbers.every(n => Number.isSafeInteger(n) && n <= max)) fail("Each face must be a whole number from 1 to the chosen die size.");
    return numbers.reduce((a, b) => a + b, 0);
  }
  function advantage(base, choices) {
    let d = base;
    if (choices.length > gifts.length) fail("The worked build in rule 123 stops after four illustrated advantages.");
    const log = [];
    choices.forEach((label, i) => {
      if (!gifts[i].includes(label)) fail("Choose a listed advantage at each step, in order.");
      const old = d;
      d = finite(d * (1 + 1 / (i + 1)));
      log.push(label + " · " + fmt(old) + " × (1 + 1/" + (i + 1) + ") = " + fmt(d) + " C2 DP");
    });
    return {dp: d, log};
  }
  function years(ls) {
    const c3 = convert(ls, "C2", "C3"), multiplier = ls < 20 ? 22 - ls : 2;
    return {value: finite(c3 * multiplier), c3, multiplier};
  }
  function highRoll(dice, convention) {
    const n = numeric(dice, "the number of six-sided dice", true);
    if (!Number.isInteger(n) || n > 40) fail("Choose 1–40 whole six-sided dice for this probability demonstration.");
    if (!["66", "two-thirds"].includes(convention)) fail("Choose a threshold reading.");
    let counts = [1n];
    for (let die = 0; die < n; die += 1) {
      const next = Array(counts.length + 6).fill(0n);
      counts.forEach((count, sum) => {
        for (let face = 1; face <= 6; face += 1) next[sum + face] += count;
      });
      counts = next;
    }
    const threshold = convention === "66" ? Math.ceil(66 * 6 * n / 100) : 4 * n;
    const total = 6n ** BigInt(n);
    const pass = counts.slice(threshold).reduce((a, b) => a + b, 0n);
    return {threshold, total: total.toString(), pass: pass.toString(), probability: Number(pass) / Number(total)};
  }
  function build(a) {
    const sheet = {values: {}, rows: [], errors: []};
    const put = (key, label, value, calculation, ref, layer) => {
      sheet.rows.push({key, label, value, calculation, ref, layer});
    };
    const derive = (key, label, operation, units, calculation, ref, layer) => {
      try {
        const v = operation(); sheet.values[key] = v;
        put(key, label, fmt(v) + units, calculation, ref, layer);
        return v;
      } catch (e) {
        put(key, label, "Unresolved", e.message, ref, layer); return null;
      }
    };
    try {
      if (a.age != null && a.age !== "" && (!Number.isInteger(Number(a.age)) || Number(a.age)<0))
        fail("Enter a nonnegative whole age or leave the age field open.");
      let base, scale;
      if (a.route === "mutant") {
        scale = "C2"; base = 9;
        put("start", "Starting Psyche", "9 C2 DP", "Start the particular low-mutant example at its stated baseline.", 123, "A");
        const result = advantage(base, a.gifts || []);
        result.log.forEach((s, i) => put("gift" + i, "Advantage " + (i+1), a.gifts[i], s, 123, "A"));
        base = result.dp;
        if ((a.gifts || []).length < 3) put("stage","Build status","Intermediate state",
          "This particular Ninja Scroll example names 36 C2 DP (6 AMBS) as its lower benchmark. The first three selections reach that mark. Other campaigns can use different starting rules.",123,"A");
      } else if (a.route === "dice") {
        scale = "C1"; base = pool(a.dice, a.sides);
        put("start", "Starting Psyche", fmt(base) + " C1 DP", String(a.dice).split(",").map(s => s.trim()).join(" + ") +
          " = " + fmt(base) + ". You supply the pool and faces for the source’s tentative dice route.", 107, "A");
      } else if (a.route === "benchmark") {
        scale = a.scale; base = numeric(a.rating, "a starting Psyche", true);
        put("start", "Starting Psyche", fmt(base) + " " + scale + " DP", "Supplied character benchmark. The GM chooses the campaign magnitude.", 11, "D");
      } else fail("Choose how to establish the starting Psyche.");
      const dp = convert(base, scale, "C2", a.branch);
      const conversion = scale === "C2" ? "The rating is already in C2." : scale === "C1" || scale === "CA" ?
        "Apply f(x) = x^log₁₀(x) at each step from " + scale + " to C2." :
        "Invert the class steps from " + scale + " using the selected " + (a.branch || "coincident") + " branch.";
      sheet.values.dp = dp;
      put("dp", "Baseline", fmt(dp) + " C2 DP", conversion + " Starting numeral for this conversion: " + fmt(base) + ".", 45, "B");
      derive("c3", "Equivalent baseline", () => convert(dp,"C2","C3"), " C3 DP", fmt(dp) + "^log₁₀(" + fmt(dp) + ")", 45, "A");
      derive("ambs", "Average Mind, Body and Soul", () => Math.sqrt(dp), " AMBS", "√" + fmt(dp) + ". This leaves the three component attributes open.", 49, "A");
      if (a.defaultPair) {
        const s = split(dp, a.trade, a.amount);
        sheet.values.ls = s.ls; sheet.values.pl = s.pl;
        const arithmetic = (key) => a.trade === "none" ? "Use the selected default LS = PL = DP." :
          fmt(dp) + (a.trade === "add" ? key === "pl" ? " + " : " − " : key === "pl" ? " × " : " ÷ ") + fmt(Number(a.amount));
        put("pl", "Power level", fmt(s.pl) + " C2 PL", arithmetic("pl"), a.trade === "none" ? 23 : 3, a.trade === "none" ? "B":"A");
        put("ls", "Life span", fmt(s.ls) + " C2 LS", arithmetic("ls"), a.trade === "none" ? 23 : 3, a.trade === "none" ? "B":"A");
        derive("years","Lifespan projection",() => years(s.ls).value, " years",
          "Convert " + fmt(s.ls) + " C2 LS to C3, then multiply by " +
          fmt(s.ls < 20 ? 22-s.ls : 2) + " using the below-20 or at-least-20 branch. Calendar projection, not a timer.",6,"B");
      } else {
        put("pair","Power level and lifespan","Unresolved","Choose whether to begin from an equal default pair before applying a trade.",23,"B");
      }
      if (a.power === "running")
        derive("speed","Reference running speed",() => finite(10 ** (dp/10-1)), " mph","10^("+fmt(dp)+"/10 − 1), choosing the DP input permitted by rule 39.",39,"A");
      else if (a.power === "camouflage")
        put("capability","Camouflage",a.route === "mutant" && a.gifts.includes("Camouflage") ? "Selected in step 3" : "Acquisition unresolved",
          "Rule 123 lists the effect in the third choice. No duration or detection test is given there.",123,"A");
      else if (a.power === "phase") {
        const matches = dp === 40 && sheet.values.pl === 80 && sheet.values.ls === 20;
        put("capability","Desolidification", matches ? "Matches the worked configuration" : "Outside the worked configuration",
          "Rule 183 illustrates 40 C2 DP → 80 C2 PL and 20 C2 LS. Other configurations and a wall-specific test remain unresolved.",183,"A");
      } else if (a.power === "time-sight") {
        const matches = c1 => Math.abs(dp-convert(c1,"C1","C2")) <= 1e-9;
        let label="No matching case established";
        if(matches(40)) label="Matches the two-direction 40 C1 example";
        else if(matches(30)) label="Matches a disputed 30 C1 alternative";
        put("capability","Two-direction time perception",label,
          "Rule 183 illustrates both directions at 40 C1 DP, then mentions the stunt at 30 C1. Its printed 152.02 C3 is the C2 result under rule 45, and the scope of that alternative is uncertain. Neither grants a general success threshold or the information received.",183,matches(30)?"C":"A");
      } else if (a.power === "cloak") {
        if (!a.cloakSource) put("phasing","Phasing extent","Unresolved","Choose whether the unspecified total in rule 53 means DP or traded PL for this character.",53,"C");
        else {
          const total = a.cloakSource === "pl" ? sheet.values.pl : dp;
          derive("phasing","Phasing extent",() => {
            const x = numeric(total,"the selected C2 total",true)/10;
            return finite(x*(x+1)/2);
          }, "%", "X = chosen C2 "+a.cloakSource.toUpperCase()+" / 10. Extent = X(X + 1)/2. No cap or obstacle test is stated.",53,"C");
        }
      }
    } catch (error) { sheet.errors.push(error.message); }
    if (a.com != null && String(a.com).trim() !== "") {
      try {
        const com = numeric(a.com, "the supplied C2 COM allocation");
        if (com < 0) fail("A supplied COM allocation must be nonnegative.");
        put("com","Supplied appearance allocation",fmt(com)+" C2 COM","User-entered allocation on the C2 scale.",47,"D");
        if (sheet.values.pl == null) put("remainder","Power remainder","Unresolved","An active C2 PL is needed before subtracting COM.",6,"B");
        else {
          if (com > sheet.values.pl) fail("The supplied COM allocation exceeds the working C2 PL.");
          sheet.values.remainder = sheet.values.pl-com;
          put("remainder","Power remainder",fmt(sheet.values.remainder)+" C2",fmt(sheet.values.pl)+" C2 PL − "+fmt(com)+" C2 COM. Local reading of the rule 47 split.",6,"B");
        }
      } catch(error) {sheet.errors.push(error.message);}
    }
    if (a.limitation) put("limit","Limitation",a.limitation,"User-supplied description. Rule 138 distinguishes the direction of point consumption and gives no universal price for this entry.",138,"D");
    return sheet;
  }
  const api = {convert, split, pool, advantage, years, highRoll, build, runDemo, fmt, gifts};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document === "undefined") return;
  function el(tag, text, klass) {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = text;
    if (klass) n.className = klass;
    return n;
  }
  function ref(n, layer) {
    const link = el("a",layer+" · #"+n); link.href = "catalogue.html#rule-"+n; return link;
  }
  function read(form) { return Object.fromEntries(new FormData(form)); }
  function makeBuilder(form) {
    const output = document.querySelector("#built-sheet");
    const fixtures = JSON.parse(document.getElementById("character-presets").textContent);
    const input = name => form.elements.namedItem(name);
    function apply(preset) {
      form.reset();
      if (!preset) {render(); return;}
      const a = preset.inputs;
      for (const key of ["name","age","route","scale","rating","dice","sides","trade","amount","power","limitation","branch","com"])
        if (input(key)) input(key).value = a[key] ?? "";
      input("concept").value = preset.concept;
      input("defaultPair").checked = a.defaultPair;
      a.gifts.forEach((g,i) => input("gift"+(i+1)).value = g);
      render();
    }
    function render() {
      const a = read(form);
      a.defaultPair = input("defaultPair").checked;
      const choices = [1,2,3,4].map(i => input("gift"+i).value);
      const stop = choices.indexOf("");
      a.gifts = choices.slice(0,stop === -1 ? choices.length : stop);
      document.querySelectorAll("[data-route]").forEach(x => x.hidden = x.dataset.route !== a.route);
      document.querySelectorAll("[data-gift-index]").forEach(x => {
        const n=Number(x.dataset.giftIndex); x.hidden=stop >= 0 && n>stop;
      });
      document.querySelector("[data-trade-options]").hidden = !a.defaultPair;
      document.querySelector("[data-trade-amount]").hidden = !a.defaultPair || a.trade === "none";
      document.querySelector("[data-inverse]").hidden = a.route !== "benchmark" || !["C3","C4"].includes(a.scale);
      document.querySelector("[data-cloak-source]").hidden = a.power !== "cloak";
      const answer=build(a);
      output.replaceChildren(el("h2",a.name || "Unnamed character"));
      output.append(el("p",[a.age ? "Age "+a.age : "Age unrecorded",powerNames[a.power]].join(" · "),"fine"));
      if (a.concept) output.append(el("p",a.concept));
      const dl=el("dl",undefined,"tool-results");
      for (const row of answer.rows) {
        const dt=el("dt",row.label), dd=el("dd");
        const strong=el("strong",row.value); strong.dataset.key=row.key; dd.append(strong,el("span",row.calculation),ref(row.ref,row.layer));
        dl.append(dt,dd);
      }
      output.append(dl);
      for (const message of answer.errors) output.append(el("p",message,"tool-error"));
      output.append(el("p","Unassigned fields · " +
        (a.com == null || a.com === "" ? "COM and the remaining allocation. " : "") +
        "Individual Mind, Body and Soul, an injury track, recovery and advancement require further rules or explicit referee decisions.","fine"));
    }
    form.addEventListener("input",render);
    document.querySelector("#clear-builder").addEventListener("click",() => {
      document.querySelector("#preset").selectedIndex=0; apply(null);
      history.replaceState(null,"",location.pathname);
    });
    document.querySelector("#load-preset").addEventListener("click",() => apply(fixtures.find(r=>r.id===document.querySelector("#preset").value)));
    const id=new URLSearchParams(location.search).get("character");
    const selected=fixtures.find(r=>r.id===id);
    if (selected) document.querySelector("#preset").value=id;
    apply(selected);
  }
  function runDemo(kind, a) {
    let result, work, bars=[];
    if (kind==="scale") {
      const v=convert(a.rating,a.from,a.to,a.branch);
      result=fmt(v)+" "+a.to;
      const steps=classes.indexOf(a.to)-classes.indexOf(a.from);
      work=steps===0?"Same class and same numeral.":steps>0?
        "With u = log₁₀("+a.rating+"), the result is 10 raised to u raised to "+(2**steps)+". Preserve the statistic’s meaning.":
        "Reversing "+(-steps)+" step(s) gives 10 raised to ±(log₁₀("+a.rating+"))^(1/"+(2**(-steps))+").";
    } else if (kind==="trade") {
      const d=numeric(a.dp,"C2 DP",true), s=split(d,a.operation,a.amount);
      result=fmt(s.pl)+" C2 PL · "+fmt(s.ls)+" C2 LS";
      work=a.operation==="add" ? "PL = "+fmt(d)+" + "+a.amount+". LS = "+fmt(d)+" − "+a.amount+". The sum is preserved." :
        "PL = "+fmt(d)+" × "+a.amount+". LS = "+fmt(d)+" ÷ "+a.amount+". The product is preserved.";
      try { const life=years(s.ls);work+=" Rule 6 branch: "+fmt(life.c3)+" C3 LS × "+fmt(life.multiplier)+" = "+fmt(life.value)+" years."; }
      catch(e){work+=" Life span in years is outside the calculator’s numerical range.";}
      bars=[["Default Psyche",d],["Power level",s.pl],["Life span",s.ls]];
    } else if(kind==="speed") {
      const d=numeric(a.dp,"a C2 rating",true);
      if (a.law==="running") {
        const v=finite(10**(d/10-1)); result=fmt(v)+" mph";
        work="Rule 39 gives 10^("+fmt(d)+"/10 − 1). This relation can use DP or PL at C2.";
      } else {
        const v=convert(d,"C2","C3"); result=fmt(v)+" mph";
        work="For a mutant, rule 64 takes the C3 numeral as mph. The C3 equivalent of "+fmt(d)+" C2 DP is "+fmt(v)+".";
      }
    } else if(kind==="advantages") {
      const n=numeric(a.count,"the number of choices");
      if(!Number.isInteger(n)||n<0||n>4)fail("Choose zero through four steps.");
      const r=advantage(9,gifts.slice(0,n).map(g=>g[0]));
      result=fmt(r.dp)+" C2 DP · "+fmt(Math.sqrt(r.dp))+" AMBS";
      work=r.log.length?r.log.join(" · ") : "No advantage selected. The source template starts at 9 C2 DP.";
      bars=[["Start",9],...Array.from({length:n},(_,i)=>["Choice "+(i+1),9*(i+2)])];
    } else if(kind==="damage") {
      const d=numeric(a.rating,"the game rating",true);
      const v=a.law==="mutant"?(d/10)**2:Math.sqrt(d)-(a.law==="subtract"?1:0);
      if(!Number.isFinite(v)||v<0)fail("This input does not produce a nonnegative finite dice count.");
      result=fmt(v)+"d6"+(Number.isInteger(v)?"":" · fractional pool");
      work=(a.law==="mutant"?"N = ("+fmt(d)+" C2 DP / 10)².":
        "N = √("+fmt(d)+" C3 PL)"+(a.law==="subtract"?" − 1.":"."))+
        (Number.isInteger(v)?" The source gives no common rule that turns this pool into an injury.":" There is no standard die with this fractional count and no rounding instruction here.");
    } else if(kind==="roll") {
      if(a.law==="under") {
        const y=numeric(a.c3,"the C3 target",true), b=numeric(a.baseline,"the starting C2 baseline",true);
        const x=convert(y,"C3","C2",a.branch), t=Math.round(x-b);
        result=fmt(t)+" or less";
        work="Convert "+fmt(y)+" C3 to "+fmt(x)+" C2, subtract "+fmt(b)+", then round. A target outside the selected dice range cannot function as an ordinary roll. At 35 C3 with baseline 10, the source prints 8; the increasing-branch replay gives 7. The dice distribution here is unspecified.";
      } else {
        const r=highRoll(a.count,a.law);
        result=fmt(100*r.probability)+"% chance on fair dice";
        work="At least "+r.threshold+" on "+a.count+"d6. Exactly "+r.pass+" of "+r.total+" equiprobable ordered outcomes satisfy this threshold. The percentage-of-maximum denominator is an assumption (C).";
        bars=[["Success",100*r.probability],["Below threshold",100*(1-r.probability)]];
      }
    }
    return {result,work,bars};
  }
  function demoForm(form) {
    const output=form.querySelector("output");
    const render=()=>{
      const a=read(form), kind=form.dataset.demo;
      form.querySelectorAll("[data-roll-input]").forEach(x=>x.hidden=(a.law==="under")!==(x.dataset.rollInput==="under"));
      try {
        const r=runDemo(kind,a);
        output.replaceChildren(el("strong",r.result),el("span",r.work));
        if(r.bars.length) {
          const chart=el("div",undefined,"meter-chart");
          const denominator=kind==="roll"?100:Math.max(...r.bars.map(i=>i[1]));
          for(const [label,value] of r.bars){
            const line=el("div",undefined,"meter-row");
            const track=el("span",undefined,"meter-track"),bar=el("i");bar.style.width=100*value/denominator+"%";track.append(bar);
            line.append(el("span",label),track,el("b",fmt(value)+(kind==="roll"?"%":"")));chart.append(line);
          }
          output.append(chart);
        }
      } catch(error){output.replaceChildren(el("span",error.message,"tool-error"));}
    };
    form.addEventListener("input",render);form.addEventListener("reset",()=>setTimeout(render,0));render();
  }
  function boot() {
    document.querySelectorAll("form.tool-form").forEach(form=>form.addEventListener("submit",event=>event.preventDefault()));
    if (document.querySelector("#character-builder")) makeBuilder(document.querySelector("#character-builder"));
    document.querySelectorAll("form[data-demo]").forEach(demoForm);
    document.querySelectorAll("[data-print]").forEach(button=>button.addEventListener("click",()=>{
      const region=document.getElementById(button.dataset.print);
      if(!region)return;
      document.body.classList.add("tool-printing");region.classList.add("print-target");
      window.print();
    }));
    window.addEventListener("afterprint",()=>{
      document.body.classList.remove("tool-printing");
      document.querySelectorAll(".print-target").forEach(n=>n.classList.remove("print-target"));
    });
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",boot);else boot();
})();
