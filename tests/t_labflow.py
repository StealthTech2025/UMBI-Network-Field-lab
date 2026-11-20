import sys, json, time
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9340)
TYPE = r'''
(function(lid){
  var run = NP_KIT.S.lab[lid]; if(!run) return 'no run';
  var typed=0, errs=[];
  run.def.solution.forEach(function(blk){
    var tab = document.querySelector('[data-act=labtab][data-dev="'+blk.dev+'"]'); if (tab) tab.click();
    blk.lines.forEach(function(line){
      if (/^\s*#/.test(line)) return;               /* skip note lines */
      var inp = document.getElementById('termin'); if(!inp){ errs.push('no terminal'); return; }
      inp.value = line; inp.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); typed++;
    });
  });
  run.def.tasks.forEach(function(t){
    if (t.type!=='answer') return;
    var sel = document.querySelector('select[data-act=labanswer][data-t="'+t.id+'"]'); if(!sel){ errs.push('no select '+t.id); return; }
    sel.value = t.correct(run.net); sel.dispatchEvent(new Event('change',{bubbles:true}));
  });
  return typed+' lines typed '+errs.join(';');
})
'''
def lab(lid):
    c.js(f"NP_KIT.S.tab['{lid}']='lab'; if(location.hash!=='#{lid}') location.hash='#{lid}'; else NP_KIT.render(); 1"); c.pump(0.4)
    st = c.js("(function(){var b=document.querySelector('[data-act=labstart][data-mode=graded]'); if(!b) return 'no graded start'; b.click(); return 'ok'})()")
    if st != 'ok': return st
    c.pump(0.4)
    t = c.js(TYPE + f"('{lid}')"); c.pump(0.3)
    c.js("(function(){var b=document.querySelector('[data-act=labsubmitask]'); if(b) b.click(); return 1})()"); c.pump(0.4)
    m = c.js("(function(){var b=document.querySelector('[data-act=labsubmitgo]')||Array.from(document.querySelectorAll('.modal button, [role=dialog] button')).filter(function(x){return /submit/i.test(x.innerText)})[0]; if(b){b.click(); return 'confirmed'} return 'no confirm'})()"); c.pump(0.4)
    rec = c.js(f"JSON.stringify((function(r){{return {{best:r.best,n:(r.attempts||[]).length,per:(r.attempts||[]).slice(-1)[0]&&r.attempts.slice(-1)[0].per}}}})(NP_KIT.labRec('{lid}')))")
    return f'{t} | {m} | {rec}'
try:
    c.js("NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); localStorage.setItem('umbi-netplus-class-v1', JSON.stringify({start:'2026-11-16',openAll:true})); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); c.pump(1); c.errors()
    for lid in json.loads(c.js("JSON.stringify(LESSONS.map(function(l){return l.id}))")):
        r = lab(lid)
        bad = '"best":100' not in r
        print(('!! ' if bad else 'ok ') + lid, r[:300])
        e = c.errors()
        if e: print('   ERR', e)
finally:
    proc.terminate()
