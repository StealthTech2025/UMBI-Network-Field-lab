import sys, json, time
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9337)
def settle(t=0.6):
    c.pump(t)
def show(label):
    txt = c.js("(function(){var a=document.getElementById('app')||document.querySelector('main')||document.body;var t=a.innerText;return JSON.stringify({len:t.length, bad:(t.match(/\\bundefined\\b|\\bNaN\\b|\\[object Object\\]|\\bnull\\b(?! *route)/g)||[]).slice(0,5), ctx:(function(){var m=t.search(/\\bundefined\\b|\\bNaN\\b|\\[object Object\\]/);return m<0?'':t.slice(Math.max(0,m-80),m+40)})(), head:t.slice(0,90).replace(/\\s+/g,' ')})})()")
    d = json.loads(txt)
    errs = c.errors()
    flag = errs or d['bad'] or d['len'] < 60
    print(('!! ' if flag else 'ok ') + label.ljust(28), d['len'], '|', d['head'][:70])
    if d['bad']: print('     odd text:', d['bad'], '…', d['ctx'].replace('\n',' '))
    for e in errs: print('     ', e)
try:
    # open all weeks, set a name
    c.js("localStorage.setItem('umbi-netplus-class-v1', JSON.stringify({start:'2026-11-16',openAll:true})); NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); settle(1); c.errors()
    routes = c.js("JSON.stringify(['home','w1','w2','w3','w4','w5','pbq','grid','rooms','cli','instmode','instructor'].concat(window.NP_PLUS && NP_PLUS.routes ? NP_PLUS.routes : []))")
    plus = c.js("(function(){var r=[];['gear','training','examprep','helpdesk','certguide','toolkit','arcade','profile','sandbox','resources','ports','dojo','leaderboard','notebook','terms','glossary','badges','labs','videos','gradebook','grades','subnet','calc','cards','flashcards'].forEach(function(x){ if(window.NP_PLUS&&NP_PLUS.handles(x)) r.push(x); }); return JSON.stringify(r);})()")
    allr = json.loads(routes) + [x for x in json.loads(plus) if x not in json.loads(routes)]
    print('routes:', allr)
    for r in allr:
        c.js(f"location.hash='#{r}'; 1"); settle(); show('#'+r)
    lessons = json.loads(c.js("JSON.stringify(LESSONS.map(function(l){return l.id}))"))
    for lid in lessons:
        for tab in ['learn','video','quiz','lab']:
            c.js(f"NP_KIT.S.tab['{lid}']='{tab}'; if(location.hash!=='#{lid}') location.hash='#{lid}'; else NP_KIT.render(); 1"); settle(0.4); show(f'#{lid} {tab}')
    c.js("location.hash='#home';1"); settle()
finally:
    proc.terminate()
