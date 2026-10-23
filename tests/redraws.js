// tests/redraws.js (node; needs playwright): every screen and its animations under constant redraws (every 120 ms): each element's opacity and
// vertical offset are sampled every frame; a fade or slide that goes backwards (restarts) or skips
// ahead is reported.
const { chromium } = require('playwright');
let failed=false;
const { spawn } = require('child_process'), path = require('path');
const server = spawn('python3', ['-m', 'http.server', '8791'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
(async()=>{await new Promise(r=>setTimeout(r, 800));const b=await chromium.launch();const p=await b.newPage({viewport:{width:360,height:740}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
const cj=require('fs').readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'),'utf8');await p.route('**/*',r=>{const u=r.request().url();if(u.startsWith('http://localhost'))return r.continue();if(u.includes('chess.js'))return r.fulfill({body:cj,contentType:'application/javascript'});return r.abort();});
await p.goto('http://localhost:8791/');await p.waitForTimeout(2500);
const sample=async(label, ms, setup)=>{
  const res=await p.evaluate(async([ms,setup])=>{
    if(setup) (0,eval)(setup);
    const key=(e,i)=>e.id?'#'+e.id:[...e.classList].filter(c=>!['fade-in','pulse-now','redrawing','pending','data-wait'].includes(c)).sort().join('.')+'@'+i;
    const snap=()=>{const out={};const counts={};document.querySelectorAll('#app *').forEach(e=>{if(e.closest('.ghost')||e.closest('svg'))return;const b=[...e.classList].filter(c=>!['fade-in','pulse-now'].includes(c)).sort().join('.');if(!e.id&&!b)return;const k=e.id?'#'+e.id:b+'@'+(counts[b]=(counts[b]||0)+1);const cs=getComputedStyle(e);if(cs.animationName==='none'&&!e.style.animation)return;const m=cs.transform.match(/,\s*(-?[\d.]+)\)$/);out[k]=[+cs.opacity,m?+m[1]:0]});return out};
    const iv=setInterval(()=>render(),120);const frames=[];const t0=performance.now();
    await new Promise(res=>{const f=()=>{frames.push([performance.now()-t0,snap()]);if(performance.now()-t0<ms)requestAnimationFrame(f);else res()};f()});clearInterval(iv);
    const issues=[];const last={};
    for(const [t,s] of frames){for(const k in s){const [o,y]=s[k];if(k in last){const [o0,y0,t0]=last[k];if(t-t0<40){if(o0-o>0.25&&o0<0.99)issues.push(Math.round(t)+' '+k+' opacity '+o0.toFixed(2)+'→'+o.toFixed(2));if(o-o0>0.45)issues.push(Math.round(t)+' '+k+' jump '+o0.toFixed(2)+'→'+o.toFixed(2));}}last[k]=[o,y,t]}}
    return {frames:frames.length, animated:Object.keys(Object.assign({},...frames.map(f=>f[1]))).length, issues:issues.slice(0,8)};},[ms,setup]);
  console.log(label, res.issues.length ? 'FAIL '+JSON.stringify(res.issues) : 'ok'); if(res.issues.length) failed=true;};
await sample('home (data fading in)', 2500, "progressJustLoaded=true; render();");
for(const [label,go] of [['profile',"screen='account';render();"],['settings',"screen='settings';settingsRebuild=true;render();"]]){ await p.evaluate(()=>{screen='home';render()}); await sample(label, 1500, go); }
for(const a of ['imbalances','analysis','candidates','final']){
  await p.evaluate(()=>{screen='home';render()});await p.click('.card[data-go="'+a+'"]');
  await sample(a+' question', 3500);
  // answer and check: the review's reveal
  await p.evaluate((a)=>{const s=st(a);if(a==='imbalances'){s.asp.material=1;s.aspTouched=true}if(a==='analysis')s.barMoved=true;if(a==='final')s.swapped=true;if(a==='candidates'){const c=new Chess(pos().fen);const m=c.moves({verbose:true})[0];s.picks.push({id:'c_'+m.from+m.to,san:m.san,from:m.from,to:m.to,uci:m.from+m.to+(m.promotion||''),slot:0})}render();},a);
  await p.waitForTimeout(300);await p.evaluate(()=>document.getElementById('check').click());
  await sample(a+' review', 5000);
}
// Dragging a move in Move selection while the page redraws every 100 ms: the drag follows the finger
// to the end and the order changes (redraws wait until it's let go).
await p.evaluate(()=>{screen='home';render()}); await p.click('.card[data-go="final"]'); await p.waitForTimeout(3500);
await p.evaluate(()=>{ window.__iv = setInterval(()=>render(), 100); });
const before = await p.evaluate(()=>st('final').order.slice());
const r1 = await (await p.$$('#ranked .rate-row'))[0].boundingBox();
await p.mouse.move(r1.x + r1.width/2, r1.y + r1.height/2); await p.mouse.down();
let lost = 0;
for(let i=1; i<=12; i++){ await p.mouse.move(r1.x + r1.width/2, r1.y + r1.height/2 + i*8); await p.waitForTimeout(60); if(!await p.evaluate(()=>!!document.querySelector('#ranked .rate-row.dragging'))) lost++; }
await p.mouse.up(); await p.waitForTimeout(300);
const after = await p.evaluate(()=>[st('final').order.slice(), document.getElementById('check').disabled]);
await p.evaluate(()=>clearInterval(__iv));
if(lost || JSON.stringify(after[0])===JSON.stringify(before) || after[1]){ console.log('drag under redraws FAIL', lost, JSON.stringify(after)); failed=true; } else console.log('drag under redraws ok');
if(errs.length){ console.log('FAIL page errors', errs); failed=true; }
await b.close(); server.kill(); console.log(failed ? 'FAIL' : 'ok'); process.exit(failed ? 1 : 0);})();
