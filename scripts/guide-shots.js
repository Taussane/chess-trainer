// scripts/guide-shots.js (node; needs playwright and the engine): the guides' example screens (learn/img/), retaken:
// each exercise's review on the guide's own position and answers, in 5 languages.
//   node scripts/guide-shots.js [en,fr,...|all] [port|land|desk] [out dir]
// Then to webp (quality 80): port and land as they are, desk cropped of its left menu (x 396..2160) and resized to
// 1520 x 1163; names: <guide>[-land|-desk][-lang].webp (see SHOTS in build-pages.py).
const only = process.argv[2] && process.argv[2]!=='all' ? process.argv[2] : null, mode = process.argv[3] || 'land';
const VP = { port:{viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2}, land:{viewport:{width:844,height:390},isMobile:true,hasTouch:true,deviceScaleFactor:2}, desk:{viewport:{width:1440,height:900},deviceScaleFactor:1.5} }[mode];
const { chromium } = require('playwright'); const fs=require('fs'), { spawn } = require('child_process'); const path=require('path'), ROOT=path.join(__dirname, '..'), S=process.argv[4] || path.join(require('os').tmpdir(), 'guide-shots');
fs.mkdirSync(S, {recursive:true});
const server = spawn('python3', ['-m','http.server',({port:'8830', land:'8831', desk:'8832'}[mode])], { cwd: ROOT, stdio:'ignore' });
const cj = fs.readFileSync(path.join(ROOT, 'vendor/chess.js/chess.js'),'utf8');
(async()=>{ await new Promise(r=>setTimeout(r,800)); const b=await chromium.launch();
 for (const lang of (only ? only.split(',') : ['en','fr','de','es','it'])) {
  for (const ex of ['imbalances','planq','candidates','final']) for (let attempt = 0; attempt < 5; attempt++) {
   const p=await b.newPage(VP); const errs=[]; p.on('pageerror',e=>errs.push(''+e));
   await p.route('**/*', r=>{ const u=r.request().url(); if(u.startsWith('http://localhost')) return r.continue(); if(u.includes('chess.js')) return r.fulfill({body:cj,contentType:'application/javascript'}); return r.abort(); });
   await p.goto('http://localhost:'+({port:'8830', land:'8831', desk:'8832'}[mode])+'/'); await p.waitForFunction(()=>typeof sfState!=='undefined' && sfState==='ready' && progressLoaded, null, {timeout:60000});
   await p.evaluate(l=>{ settings.lang=l; setLanguage(); firstVisit=null; hintsOn=false; }, lang).catch(()=>{});
   const code = { imbalances:'imbalances.g509.41', planq:'planq.g601.34', candidates:'candidates.g354.51', final:'final.g601.60' }[ex];
   // the position as a normal one (the exercise's own title, not "Shared"): the Plan finder's own object, the others in their track
   await p.evaluate(([a, c])=>{ const [, g, ply] = c.split('.'), q = masterPosAt(g, +ply);
     if(a==='planq'){ openShared(c); return; }
     openActivity(a); const t = ctx(a); orders[t][seqBy[t]] = q; store[t][q.key] = undefined; syncPos(); prefetchCurrent(); render(); }, [ex, code]);
   await p.waitForTimeout(4000);
   let info = '';
   if (ex==='imbalances') {
     await p.evaluate(()=>{ const s=st('imbalances'); s.asp={ activity:1, pawns:1, material:-1 }; render(); });
     await p.waitForTimeout(300); await p.evaluate(()=>{ const c=document.getElementById('check'); c.disabled=false; c.click(); });
   } else if (ex==='planq') {
     const click = async txt=>p.evaluate(t=>{ const b=[...document.querySelectorAll('.layer:not(.ghost) .pq-side')].find(x=>x.dataset.v===t.v && (t.f ? x.dataset.first===t.f : x.dataset.row===t.r)); if(b) b.click(); return !!b; }, txt);
     await click({f:'urgent', v:'no'}); await click({f:'winning', v:'w'}); await p.waitForTimeout(300);
     await p.evaluate(()=>document.getElementById('pqCheck').click()); await p.waitForTimeout(1500);
     await p.evaluate(()=>{ const g=document.getElementById('pqGo'); if(g) g.click(); }); await p.waitForTimeout(1500);
     info = await p.evaluate(()=>[...document.querySelectorAll('.layer:not(.ghost) .pq-side')].map(b=>b.textContent+'|'+JSON.stringify(b.dataset)).join(' ; '));
     // row 0 (trades): the right one; row 1: "Either" (0)
     await p.evaluate(()=>{ const r=planq.rows; const btn=(row,v)=>[...document.querySelectorAll('.layer:not(.ghost) .pq-side')].find(x=>x.dataset.row===row && x.dataset.d===String(v)); const a=btn('pieces', r[0].answer); if(a) a.click(); const e=btn('approach', 0); if(e) e.click(); });
     await p.waitForTimeout(300); await p.evaluate(()=>document.getElementById('pqCheck').click());
   } else if (ex==='candidates') {
     await p.evaluate(()=>{ const s=st('candidates'), c=new Chess(pos().fen); ['bxa3','Qa5','h5'].forEach((san,k)=>{ const mv=c.moves({verbose:true}).find(m=>m.san===san); s.picks.push({ id:'c_'+mv.from+mv.to, san:mv.san, from:mv.from, to:mv.to, uci:mv.from+mv.to, slot:k }); }); render(); });
     await p.waitForTimeout(300); await p.evaluate(()=>{ const c=document.getElementById('check'); c.disabled=false; c.click(); });
   } else {
     await p.waitForFunction(()=>Array.isArray(finalMoves(pos())), null, {timeout:60000});
     info = await p.evaluate(()=>{ const s=st('final'), mv=finalMoves(pos()), want=['Nxe4','Rh2','Qg2','Qh2']; const ids=want.map(w=>(mv.find(m=>m.san===w)||{}).id); if(ids.every(Boolean)) s.order=ids; render(); return mv.map(m=>m.san).join(','); });
     await p.waitForTimeout(300); await p.evaluate(()=>{ const c=document.getElementById('check'); c.disabled=false; c.click(); });
   }
   await p.waitForTimeout(9000);
   if (ex==='planq') await p.evaluate(()=>{ const h = document.querySelector('.layer:not(.ghost) h1, #app h1'); if(h) h.textContent = 'Plan finder'; });   // (as opened normally: its own title, not "Shared")
   await p.waitForTimeout(300);
   const name = { imbalances:'imbalance-reading', planq:'plan-finder', candidates:'candidate-moves', final:'move-selection' }[ex] + (mode==='port' ? '' : '-' + mode) + (lang==='en' ? '' : '-' + lang);
   // the guide's caption holds only if the engine's grades are the ones it describes (the search can vary a little)
   const ok = await p.evaluate(ex=>{ const t = document.querySelector('.layer:not(.ghost)') ? document.querySelector('.layer:not(.ghost)').innerText : document.body.innerText;
     if(ex==='candidates'){ const s = st('candidates'), r = (s.review || s.rows || null); return /h5[\s\S]{0,40}(Inaccuracy|Imprécision|Ungenauigkeit|Imprecisión|Imprecisione)/.test(t); }
     if(ex==='final') return (t.match(/Inaccuracy|Imprécision|Ungenauigkeit|Imprecisión|Imprecisione/g) || []).length===2;
     return true; }, ex);
   if(!ok && attempt < 4){ console.log('retry', lang, ex); await p.close(); continue; }
   await p.screenshot({path:`${S}/${name}.png`});
   console.log(lang, ex, info.slice(0,300), errs.join(' | ').slice(0,200));
   await p.close(); break;
  } }
 await b.close(); server.kill(); })();
