import sys, json, time
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9343)
ANSWER = r'''
(function(right){
  var L = JSON.parse(localStorage.getItem('umbi-netplus-exam-live-v1')); if(!L) return 'no live';
  var q = L.qs[L.cur];
  if (q.pbq) {
    q.items.forEach(function(it,i){
      var el = document.querySelector('[data-xp=pbqin][data-i="'+i+'"]') || document.querySelector('[data-xp=pbqsel][data-i="'+i+'"]');
      if(!el) return;
      var v = right ? it.ans : (el.tagName==='SELECT' ? (q.choices.filter(function(c){return String(c).toLowerCase()!==String(it.ans).toLowerCase()})[0]) : '1.2.3.4');
      el.value = v; el.dispatchEvent(new Event(el.tagName==='SELECT'?'change':'input',{bubbles:true})); if(el.tagName==='SELECT') el.dispatchEvent(new Event('click',{bubbles:true}));
    });
  } else {
    var want = right ? q.a : (q.a+1)%q.o.length;
    var r = document.querySelector('[data-xp=pick][data-i="'+want+'"]'); if(!r) return 'no radio at '+L.cur;
    r.click();
  }
  var nx = document.querySelector('[data-xp=next]:not([disabled])');
  if (nx) { nx.click(); return 'next'; }
  return 'last';
})
'''
def run_exam(mode, right):
    c.js("location.hash='#examprep'; 1"); c.pump(0.5)
    c.js("(function(){var h=document.querySelector('[data-xp=home]'); if(h) h.click(); return 1})()"); c.pump(0.3)
    st = c.js(f"(function(){{var b=document.querySelector('[data-xp=start][data-m={mode}]'); if(!b) return 'no start for {mode}: '+Array.from(document.querySelectorAll('[data-xp=start]')).map(function(x){{return x.getAttribute('data-m')}}).join(','); b.click(); return 'ok'}})()")
    if st != 'ok': return st
    c.pump(0.5)
    n = 0
    for i in range(120):
        r = c.js(ANSWER + f"({str(right).lower()})"); n += 1
        if r != 'next': break
    c.pump(0.3)
    c.js("(function(){var b=document.querySelector('[data-xp=reviewscr]'); if(b) b.click(); return 1})()"); c.pump(0.3)
    c.js("(function(){var b=document.querySelector('[data-xp=askend]'); if(b) b.click(); return 1})()"); c.pump(0.3)
    c.js("(function(){var b=document.querySelector('[data-xp=end]'); if(b) b.click(); return 1})()"); c.pump(0.6)
    det = json.loads(c.js("localStorage.getItem('umbi-netplus-exam-detail-v1')") or '[]')
    last = det[-1] if det else {}
    sizes = c.js("JSON.stringify(Object.keys(localStorage).reduce(function(o,k){o[k]=localStorage.getItem(k).length;return o},{}))")
    head = c.js("document.getElementById('app').innerText.slice(0,200).replace(/\\s+/g,' ')")
    return f"answered {n} screens, last={r} -> scaled {last.get('scaled')} pct {last.get('pct')} pass {last.get('pass')} qs {len(last.get('qs',[]))} | page: {head[:120]} | storage sizes {sizes}"
try:
    c.js("NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); c.pump(1); c.errors()
    modes = c.js("(function(){location.hash='#examprep'; return 1})()"); c.pump(0.5)
    print('modes:', c.js("Array.from(document.querySelectorAll('[data-xp=start]')).map(function(x){return x.getAttribute('data-m')}).join(',')"))
    print('full, all right :', run_exam('full', True)); print('  errors', c.errors())
    print('full, all wrong :', run_exam('full', False)); print('  errors', c.errors())
    for k in range(4):
        print(f'half #{k+1} right   :', run_exam('half', True)[-260:])
    print('errors', c.errors())
finally:
    proc.terminate()
