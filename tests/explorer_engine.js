// tests/explorer_engine.js (node; needs playwright and the engine): the explorer opened from a position while the engine
// is idle still gets its evaluation (its search used to wait in the queue until something else woke the engine).
const { chromium } = require('playwright'); const fs=require('fs'), { spawn } = require('child_process');
const server = spawn('python3', ['-m','http.server','8799'], { cwd: require('path').join(__dirname, '..'), stdio:'ignore' });
const cj = fs.readFileSync(require('path').join(__dirname, '../vendor/chess.js/chess.js'),'utf8');
(async()=>{ await new Promise(r=>setTimeout(r,800)); const b=await chromium.launch();
 const p=await b.newPage({viewport:{width:412,height:915},isMobile:true,hasTouch:true});
 await p.route('**/*', r=>{ const u=r.request().url(); if(u.startsWith('http://localhost')) return r.continue(); if(u.includes('chess.js')) return r.fulfill({body:cj,contentType:'application/javascript'}); return r.abort(); });
 await p.goto('http://localhost:8799/'); await p.waitForFunction(()=>typeof sfState!=='undefined' && sfState==='ready' && progressLoaded, null, {timeout:60000});
 await p.evaluate(()=>{ firstVisit=null; routine=false; openActivity('imbalances'); });
 await p.waitForFunction(()=>!sfBusy && !sfQueue.length && !bgQueue.length, null, {timeout:90000}).catch(()=>console.log('never idle'));
 const fen = await p.evaluate(()=>{ exploreFrom(curPos, 'imbalances'); return explorer.fens[explorer.at]; });
 const ok = await p.waitForFunction(f=>explorerEvals[f] && explorerEvals[f].status==='done', fen, {timeout:20000}).then(()=>true).catch(()=>false);
 console.log(ok ? 'ok' : 'FAIL: the explorer never got its evaluation'); await b.close(); server.kill(); process.exit(ok ? 0 : 1);
 await b.close(); server.kill(); })();
