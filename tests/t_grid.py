import sys, json, time
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9341)
PLAY = r'''
(function(mid){
  function q(s){return document.querySelector(s)}
  var b = q('[data-grid=brief][data-m="'+mid+'"]'); if(!b) return 'no brief button (locked?)';
  b.click();
  var s = q('[data-grid=start]'); if(!s) return 'no start: '+document.getElementById('app').innerText.slice(0,200);
  s.click();
  var run = NP_KIT.S.lab.grid; if(!run) return 'no run';
  var typed = 0, rej = [];
  run.def.solution.forEach(function(blk){
    var tab = q('[data-grid=tab][data-dev="'+blk.dev+'"]'); if (tab && run.active!==blk.dev) tab.click();
    blk.lines.forEach(function(line){
      if (/^\s*#/.test(line)) return;
      var inp = q('#gtermin'); if(!inp){ rej.push('no terminal'); return; }
      inp.value=line; inp.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); typed++;
    });
  });
  var asked = 0;
  run.def.tasks.forEach(function(t){
    if (t.type!=='answer') return;
    var want = t.correct(run.net);
    var btn = Array.from(document.querySelectorAll('[data-grid=ask][data-t="'+t.id+'"]')).filter(function(x){return x.getAttribute('data-v')===want})[0];
    if (btn) { btn.click(); asked++; } else rej.push('no ask button for '+t.id+' = '+want);
  });
  var ck = q('[data-grid=check]'); if (ck) ck.click();
  var g = JSON.parse(localStorage.getItem('umbi-netplus-grid-v1')||'{}');
  var txt = document.getElementById('app').innerText;
  return JSON.stringify({typed:typed, asked:asked, done: g.done && g.done[mid], xp:g.xp, view: NP_KIT.S.gridView, result: run.result ? Object.keys(run.result).join(',') : null, rej: rej.slice(0,3), head: txt.slice(0,160).replace(/\s+/g,' ')});
})
'''
try:
    c.js("NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); localStorage.setItem('umbi-netplus-class-v1', JSON.stringify({start:'2026-11-16',openAll:true})); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); c.pump(1); c.errors()
    c.js("location.hash='#grid';1"); c.pump(0.6)
    print('hub errors', c.errors())
    mids = [f'm{i}' for i in range(1, 29)]
    for mid in mids:
        c.js("NP_KIT.S.gridView='hub'; NP_KIT.render(); 1"); c.pump(0.3)
        r = c.js(PLAY + f"('{mid}')"); c.pump(0.5)
        r2 = c.js("JSON.stringify({done: (JSON.parse(localStorage.getItem('umbi-netplus-grid-v1')||'{}').done||{}), view: NP_KIT.S.gridView})")
        d2 = json.loads(r2)
        ok = mid in d2['done']
        print(('ok ' if ok else '!! ') + mid, r if isinstance(r,str) else r, '| done:', d2['done'].get(mid), 'view:', d2['view'])
        e = c.errors()
        if e: print('   ERR', e)
    # Port Runner
    c.js("NP_KIT.S.gridView='hub'; NP_KIT.render(); 1"); c.pump(0.3)
    c.js("document.querySelector('[data-grid=runner]').click();1"); c.pump(0.6)
    print('runner screen:', c.js("document.getElementById('app').innerText.slice(0,300).replace(/\\s+/g,' ')"))
    for i in range(5):
        c.js("(function(){var i=document.getElementById('runin'); if(!i) return 0; i.value='80'; i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); return 1})()"); c.pump(0.2)
    c.js("(function(){var b=document.querySelector('[data-grid=runnerend]'); if(b) b.click(); return 1})()"); c.pump(0.5)
    print('runner end:', c.js("document.getElementById('app').innerText.slice(0,300).replace(/\\s+/g,' ')"))
    print('runner errors', c.errors())
    g = json.loads(c.js("localStorage.getItem('umbi-netplus-grid-v1')"))
    print('grid save: xp', g.get('xp'), 'done', len(g.get('done', {})), 'runner', g.get('runner'))
finally:
    proc.terminate()
