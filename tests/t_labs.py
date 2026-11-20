import sys, json
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9334)
JS = r'''
(function(){
 var out = {};
 Object.keys(LABS).forEach(function(lid){
  var fails = {}, errs = {}, cmdErr = {}, n = 0;
  for (var seed = 1; seed <= 25; seed++) {
   var s = seed * 7919 + 13;
   try {
    var def = LABS[lid](s), net = def.build(), sessions = {};
    (def.devices||[]).forEach(function(id){ sessions[id] = new NET.DeviceSession(net, id); });
    (def.pcs||[]).forEach(function(p){ sessions[p] = new NET.HostSession(net, p); });
    var cmds = [];
    (def.solution||[]).forEach(function(blk){
      var sess = sessions[blk.dev];
      if (!sess) { errs['no session '+blk.dev] = (errs['no session '+blk.dev]||0)+1; return; }
      blk.lines.forEach(function(line){
        var o = sess.run(line); cmds.push([blk.dev, line.trim()]);
        if (o && /^%|not recognized|command not found|Invalid input|Incomplete command|Unknown command/i.test(o)) { var k = blk.dev+': '+line.trim().replace(/\d+/g,'#')+' => '+String(o).split('\n')[0].slice(0,80); cmdErr[k]=(cmdErr[k]||0)+1; }
      });
    });
    def.tasks.forEach(function(t){
      var ok;
      try {
        if (t.type === 'answer') ok = t.options.indexOf(t.correct(net)) >= 0;  /* correct answer must be one of the options */
        else if (t.type === 'cmd') ok = cmds.some(function(c){ return t.re.test(c[1]); });
        else ok = !!t.check(net);
      } catch (e) { ok = false; errs[t.id+': '+e.message] = (errs[t.id+': '+e.message]||0)+1; }
      if (!ok) fails[t.id+' '+t.text.replace(/\d+/g,'#').slice(0,90)] = (fails[t.id+' '+t.text.replace(/\d+/g,'#').slice(0,90)]||0)+1;
    });
    n++;
   } catch (e) { errs['build/run: '+e.message] = (errs['build/run: '+e.message]||0)+1; }
  }
  out[lid] = {runs:n, fails:fails, errs:errs, cmdErr:cmdErr};
 });
 return JSON.stringify(out);
})()
'''
try:
    r = json.loads(c.js(JS))
    for lid, v in r.items():
        bad = v['fails'] or v['errs'] or v['cmdErr']
        print(('FAIL ' if bad else 'ok   ') + lid, v['runs'], 'runs')
        for k, cnt in v['fails'].items(): print('    task fails', cnt, 'x', k)
        for k, cnt in v['errs'].items(): print('    error', cnt, 'x', k)
        for k, cnt in v['cmdErr'].items(): print('    solution cmd rejected', cnt, 'x', k)
    print('page errors:', c.errors())
finally:
    proc.terminate()
