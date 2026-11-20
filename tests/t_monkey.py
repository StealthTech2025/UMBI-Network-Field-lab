import sys, json, time, random
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9342)
MONKEY = r'''
(function(seed, steps){
  var s = seed; function rnd(){ s = (s*9301+49297)%233280; return s/233280; }
  var log = [], route0 = location.hash;
  var words = ['80','443','ping 10.0.0.1','ipconfig','show ip interface brief','nmap 10.0.0.5','help','tcp','udp','255.255.255.0','22','dig example.com','cat flag.txt','enable','configure terminal','exit','yes','10.0.0.1','A','DNS'];
  for (var i=0;i<steps;i++){
    if (location.hash !== route0) { location.hash = route0; }
    var app = document.getElementById('app'); if(!app) break;
    var els = Array.from(app.querySelectorAll('button:not([disabled]), a[href^="#"], [data-act], [data-grid], [data-arc], input:not([type=hidden]), select, textarea')).filter(function(e){ var r=e.getBoundingClientRect(); return r.width>0 && r.height>0 && !/^https?:/.test(e.getAttribute('href')||''); });
    /* never let the monkey wipe progress or leave the module via reset buttons */
    els = els.filter(function(e){ return !/reset|delete|clear (all|progress)|forget|sign out|log ?out/i.test(e.innerText||e.value||''); });
    if (!els.length) { log.push('nothing clickable'); break; }
    var e = els[Math.floor(rnd()*els.length)];
    var tag = e.tagName;
    try {
      if (tag==='INPUT' || tag==='TEXTAREA') {
        if (e.type==='radio' || e.type==='checkbox') e.click();
        else { e.value = words[Math.floor(rnd()*words.length)]; e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}));
          e.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
          var f = e.form; if (f && document.body.contains(f)) { if (f.requestSubmit) f.requestSubmit(); } }
      } else if (tag==='SELECT') { var o=e.options; if(o.length>1){ e.selectedIndex = 1+Math.floor(rnd()*(o.length-1)); e.dispatchEvent(new Event('change',{bubbles:true})); } }
      else e.click();
    } catch(err) { log.push('step '+i+' '+(e.innerText||e.id||tag).slice(0,40)+': '+err.message); }
  }
  return JSON.stringify(log.slice(0,10));
})
'''
try:
    c.js("NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); localStorage.setItem('umbi-netplus-class-v1', JSON.stringify({start:'2026-11-16',openAll:true})); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); c.pump(1); c.errors()
    # Port Runner done properly
    c.js("location.hash='#grid';1"); c.pump(0.5)
    c.js("document.querySelector('[data-grid=runner]').click();1"); c.pump(0.5)
    for ans in ['3389','rdp','80','53','tcp']:
        c.js(f"(function(){{var i=document.getElementById('runin'); i.value='{ans}'; document.getElementById('runform').requestSubmit(); return 1}})()"); c.pump(0.3)
    print('runner mid:', c.js("document.getElementById('app').innerText.slice(0,200).replace(/\\s+/g,' ')"))
    c.js("document.querySelector('[data-grid=runnerend]').click();1"); c.pump(0.4)
    print('runner end:', c.js("document.getElementById('app').innerText.slice(0,160).replace(/\\s+/g,' ')"), c.errors())
    for r in ['arcade','training','helpdesk','examprep','pbq','rooms','sandbox','ports','gear','certguide','toolkit','profile','resources','cli','home','w1','w3','w1-l1','w2-l4','w5-l4','grid','instmode']:
        tot = []
        for seed in (11, 23, 37):
            c.js(f"location.hash='#{r}'; NP_KIT.render && NP_KIT.render(); 1"); c.pump(0.3)
            out = c.js(MONKEY + f"({seed}, 120)"); c.pump(0.4)
            errs = c.errors()
            if out and out != '[]': tot.append('monkey: ' + str(out))
            tot += errs
        uniq = []
        for e in tot:
            k = e.split('\n')[0][:200]
            if k not in uniq: uniq.append(k)
        print(('!! ' if uniq else 'ok ') + '#' + r, ' | '.join(uniq)[:900])
finally:
    proc.terminate()
