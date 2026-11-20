import sys, json, time
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9339)
def run_quiz(lid, mode, correct):
    c.js(f"NP_KIT.S.tab['{lid}']='quiz'; if(location.hash!=='#{lid}') location.hash='#{lid}'; else NP_KIT.render(); 1"); c.pump(0.4)
    c.js(f"(function(){{var r=document.querySelector('[data-act=quizretry]'); if(r) r.click(); var x=Array.from(document.querySelectorAll('button')).filter(function(b){{return /close review/i.test(b.innerText)}})[0]; if(x) x.click(); return 1}})()"); c.pump(0.4)
    ok = c.js(f"(function(){{var b=document.querySelector('[data-act=quizstart][data-mode={mode}]'); if(!b) return 'no start button: '+document.querySelector('#app').innerText.slice(300,700); b.click(); return 'ok';}})()")
    if ok != 'ok': return ok
    c.pump(0.4)
    res = c.js(f"""(function(){{
      var L=LESSONS.filter(function(l){{return l.id==='{lid}'}})[0], qs=document.querySelectorAll('[data-act=qpick]'), n=0, clicked=0;
      var by={{}}; qs.forEach(function(i){{ (by[i.getAttribute('data-n')]=by[i.getAttribute('data-n')]||[]).push(i); }});
      var run = NP_KIT.S.quiz ? NP_KIT.S.quiz['{lid}'] : null;
      Object.keys(by).forEach(function(k){{
        var q = run ? L.quiz[run.qs[+k].qi] : null;
        var want = q ? q.a : 0;
        var fresh = document.querySelectorAll('[data-act=qpick][data-n="'+k+'"]'); var pick = Array.from(fresh).filter(function(i){{ return {str(correct).lower()} ? +i.getAttribute('data-o')===want : +i.getAttribute('data-o')!==want; }})[0];
        if (pick) {{ pick.click(); clicked++; }}
      }});
      return clicked + ' of ' + Object.keys(by).length;
    }})()""")
    c.pump(0.3)
    sub = c.js("(function(){var b=document.querySelector('[data-act=quizsubmit]'); if(!b) return 'no submit'; b.click(); return 'ok'})()")
    c.pump(0.4)
    # confirm modal?
    modal = c.js("(function(){var m=document.querySelector('.modal, [role=dialog]'); if(!m) return ''; var b=Array.from(m.querySelectorAll('button')).filter(function(x){return /submit|yes|confirm/i.test(x.innerText)})[0]; if(b){b.click(); return 'confirmed: '+m.innerText.slice(0,80);} return 'modal: '+m.innerText.slice(0,120)})()")
    c.pump(0.4)
    rec = c.js(f"JSON.stringify((function(r){{return {{best:r.best, n:(r.attempts||[]).length, last:(r.attempts||[]).slice(-1)[0]&&r.attempts.slice(-1)[0].s}}}})(NP_KIT.quizRec('{lid}')))")
    shown = c.js("(document.querySelector('#app').innerText.match(/\\d+%/)||[''])[0]")
    return f'{res} answered, submit {sub} {modal} -> record {rec}, page shows {shown}'
try:
    c.js("NP_KIT.S.prog.name='Test Student'; NP_KIT.save(); localStorage.setItem('umbi-netplus-class-v1', JSON.stringify({start:'2026-11-16',openAll:true})); setTimeout(function(){location.reload()},1200); 1")
    time.sleep(5); c.pump(1); c.errors()
    lessons = json.loads(c.js("JSON.stringify(LESSONS.map(function(l){return l.id}))"))
    lid = 'w1-l2'
    print(lid, 'graded all-wrong :', run_quiz(lid, 'graded', False))
    print(lid, 'graded all-wrong :', run_quiz(lid, 'graded', False))
    print(lid, 'graded all-wrong :', run_quiz(lid, 'graded', False))
    print(lid, '4th attempt      :', run_quiz(lid, 'graded', True))
    print(lid, 'practice         :', run_quiz(lid, 'practice', True))
    print('errors', c.errors())
    print('overall', c.js("JSON.stringify(NP_KIT.overall ? NP_KIT.overall() : null)"))
finally:
    proc.terminate()
