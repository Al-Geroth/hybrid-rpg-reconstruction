"use strict";
(() => {
  const graph = window.EDITION_GRAPH, select = document.getElementById("node"), panel=document.getElementById("neighbours");
  const nodes = new Map(graph.nodes.map(n=>[n.id,n]));
  function render() {
    const id=select.value;
    const edges=graph.edges.filter(e=>e.source===id || e.target===id);
    const result=document.createElement("p");
    result.textContent=edges.length+" linked relationships out of "+graph.edges.length+" graph edges.";
    const list=document.createElement("ul");list.className="entry-list";
    for(const edge of edges) {
      const item=document.createElement("li"), a=nodes.get(edge.source), b=nodes.get(edge.target);
      for(const [n,tail] of [[a," · "+edge.type+" → "],[b,""]]){
        const el=document.createElement("a");el.href=n.link;el.textContent=n.label;item.append(el,tail);
      }
      list.append(item);
    }
    panel.replaceChildren(result,list);
  }
  select.addEventListener("change",render);render();
})();
