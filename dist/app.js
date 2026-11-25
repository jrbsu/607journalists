const input=document.querySelector('#search'),results=document.querySelector('#search-results'),status=document.querySelector('#search-status');
const escapeHtml=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
input.addEventListener('input',()=>{const q=input.value.trim().toLocaleLowerCase();results.replaceChildren();if(q.length<2){status.textContent=q?'Enter at least two characters.':'';return}const matches=searchIndex.filter(p=>p.text.toLocaleLowerCase().includes(q));status.textContent=`${matches.length} matching ${matches.length===1?'passage':'passages'}`;for(const p of matches){const at=p.text.toLocaleLowerCase().indexOf(q),start=Math.max(0,at-65),end=Math.min(p.text.length,at+q.length+110),a=document.createElement('a');a.href='#'+p.id;a.innerHTML=`<strong>${escapeHtml(p.label)}</strong>${start?'…':''}${escapeHtml(p.text.slice(start,at))}<mark>${escapeHtml(p.text.slice(at,at+q.length))}</mark>${escapeHtml(p.text.slice(at+q.length,end))}…`;results.append(a)}});
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();input.focus()}if(e.key==='Escape'&&document.activeElement===input){input.value='';input.dispatchEvent(new Event('input'));input.blur()}});
if(matchMedia('(max-width:620px)').matches)document.querySelector('.contents').open=false;
const links=[...document.querySelectorAll('nav a')];function active(){links.forEach(a=>{const match=a.hash===location.hash;a.classList.toggle('active',match);if(match)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')})}addEventListener('hashchange',active);active();

// A web-font swap can move a distant target after the browser's initial jump.
// Correct once layout settles, unless the reader has started navigating away.
let anchorRevision=0;
const cancelAnchorCorrection=()=>{anchorRevision++};
addEventListener('wheel',cancelAnchorCorrection,{passive:true});
addEventListener('touchstart',cancelAnchorCorrection,{passive:true});
addEventListener('pointerdown',cancelAnchorCorrection,{passive:true});
addEventListener('keydown',e=>{if(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '].includes(e.key))cancelAnchorCorrection()});
function settleAnchor(){
 const hash=location.hash,revision=++anchorRevision;
 if(!hash||!document.fonts)return;
 if(document.readyState==='complete'&&document.fonts.status==='loaded')return;
 const fontsReady=document.fonts.ready;
 const pageReady=document.readyState==='complete'?Promise.resolve():new Promise(resolve=>addEventListener('load',resolve,{once:true}));
 Promise.all([fontsReady,pageReady]).then(()=>requestAnimationFrame(()=>{
  if(revision!==anchorRevision||location.hash!==hash)return;
  let id;try{id=decodeURIComponent(hash.slice(1))}catch{return}
  const target=document.getElementById(id);
  if(target)target.scrollIntoView({block:'start',behavior:'instant'});
 }));
}
addEventListener('hashchange',settleAnchor);
settleAnchor();
