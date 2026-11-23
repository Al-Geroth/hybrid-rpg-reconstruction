"use strict";
(() => {
  const form = document.querySelector(".filters");
  if (!form) return;
  const result = document.getElementById("matches");
  const clean = text => text.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "");
  const searchMode = form.dataset.kind === "search";
  const rows = [...document.querySelectorAll("[data-row]")];
  const controls = [...form.querySelectorAll("[name]")];
  const records = searchMode ? window.EDITION_INDEX : [];
  const searchList = document.getElementById("search-results");
  const params = new URLSearchParams(location.search);
  for (const control of controls) control.value = params.get(control.name) || "";
  function refresh(changeURL = true) {
    const current = new URLSearchParams();
    for (const field of controls) if (field.value) current.set(field.name,field.value);
    if (changeURL) history.replaceState(null, "", location.pathname + (current.size ? "?" + current : "") + location.hash);
    const words = clean(current.get("q") || "").trim().split(/\s+/).filter(Boolean);
    if (searchMode) {
      const matches = words.length ? records.filter(r => words.every(w => clean(r[1]+" "+r[2]+" "+r[3]).includes(w))) : [];
      searchList.replaceChildren();
      for (const [href,title,section,description] of matches) {
        const li = document.createElement("li");
        const a = document.createElement("a"); a.href = href; a.textContent = title;
        const tag = document.createElement("span"); tag.className = "fine"; tag.textContent = " · "+section;
        const excerpt = document.createElement("div"); excerpt.textContent = description.length > 175 ? description.slice(0,172)+"…" : description;
        li.append(a,tag,excerpt); searchList.append(li);
      }
      result.textContent = words.length ? matches.length+" matches across "+records.length+" indexed entries." : "Search chapter text, terms, equations and editorial descriptions.";
      return;
    }
    let shown = 0;
    for (const row of rows) {
      let keep = words.every(w => row.dataset.words.includes(w));
      for (const [name,value] of current) {
        if (name !== "q" && !(row.dataset[name] || "").split("|").includes(value.trim())) keep = false;
      }
      row.hidden = !keep;
      if (keep) shown++;
    }
    result.textContent = "Showing "+shown+" of "+rows.length+" "+form.dataset.kind+".";
  }
  form.addEventListener("input",() => refresh()); form.addEventListener("change",() => refresh());
  form.addEventListener("submit",event => {event.preventDefault();refresh()});
  form.addEventListener("reset",() => setTimeout(() => refresh(),0));
  refresh(false);
})();
