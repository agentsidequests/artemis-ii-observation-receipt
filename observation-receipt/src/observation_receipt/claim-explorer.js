'use strict';
// Search changes visibility only. The immutable receipt, integrity state and findings stay intact.
const ClaimExplorer = (() => {
  function match(text,status,query,filter) {
    if(!['all','supported','blocked','refuted'].includes(filter))throw Error('Unknown claim filter');
    return (filter==='all'||status===filter)&&text.toLowerCase().includes(query.trim().toLowerCase());
  }
  return {match};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=ClaimExplorer;
if(typeof document!=='undefined'&&document.getElementById('claim-tools')) {
  const root=document.getElementById('claim-tools'),search=document.getElementById('claim-search'),filter=document.getElementById('claim-filter'),cards=Array.from(document.querySelectorAll('[data-claim-card]'));
  root.hidden=false;
  function refresh() {
    let count=0;
    for(const card of cards){card.hidden=!ClaimExplorer.match(card.textContent,card.dataset.statusFamily,search.value,filter.value);if(!card.hidden)count++;}
    document.getElementById('claim-count').textContent=count+' of '+cards.length+' saved findings shown. The receipt and integrity state are unchanged.';
    document.getElementById('claim-empty').hidden=count!==0;
  }
  function reset() {search.value='';filter.value='all';refresh();search.focus();}
  search.addEventListener('input',refresh);filter.addEventListener('change',refresh);document.getElementById('claim-reset').addEventListener('click',reset);document.getElementById('claim-empty-reset').addEventListener('click',reset);
  function focusClaim() {
    if(!location.hash.startsWith('#claim='))return;
    let id;try{id=decodeURIComponent(location.hash.slice(7));}catch{document.getElementById('claim-count').textContent='Invalid claim address. All findings remain available.';return;}
    const card=cards.find(c=>c.dataset.claimCard===id);
    if(!card){document.getElementById('claim-count').textContent='Claim not found in this saved case. Clear search to inspect all findings.';return;}
    search.value='';filter.value='all';refresh();card.querySelector('details').open=true;card.focus();
  }
  window.addEventListener('hashchange',focusClaim);refresh();focusClaim();
}
