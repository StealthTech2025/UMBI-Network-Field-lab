import sys, json
sys.path.insert(0, '.')
from cdp import launch
import os
APP_URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fieldlab.html'))
proc, c = launch(APP_URL, port=9336)
JS = r'''
(function(){
 var p = [], seen = {};
 LESSONS.forEach(function(l){
  (l.quiz||[]).forEach(function(q,i){
   var tag = l.id+' Q'+(i+1);
   var multi = Array.isArray(q.a);
   if (!q.q || !Array.isArray(q.o) || q.o.length < 2) p.push(tag+': missing question/options');
   if (multi ? q.a.some(function(a){return a<0||a>=q.o.length}) : !(q.a>=0 && q.a<q.o.length)) p.push(tag+': answer index out of range '+JSON.stringify(q.a));
   var lo = q.o.map(function(o){return String(o).trim().toLowerCase()});
   if (lo.some(function(o,j){return lo.indexOf(o)!==j})) p.push(tag+': duplicate options '+JSON.stringify(q.o));
   if (!q.e) p.push(tag+': no explanation');
   var key = String(q.q).trim().toLowerCase();
   if (seen[key]) p.push(tag+': same question as '+seen[key]); else seen[key]=tag;
   var extra = Object.keys(q).filter(function(k){return ['q','o','a','e'].indexOf(k)<0});
   if (extra.length) p.push(tag+': other fields '+extra.join(','));
  });
  if ((l.quiz||[]).length < 10) p.push(l.id+': only '+(l.quiz||[]).length+' questions');
 });
 var types = {};
 NPQ.forEach(function(r,i){
  var tag='NPQ#'+i+' ('+r[1]+')';
  if (!Array.isArray(r)) { types[typeof r]=1; return; }
  var o=r[4], a=r[5], ww=r[7];
  if (!Array.isArray(o)) { p.push(tag+': options not array: '+JSON.stringify(r).slice(0,120)); return; }
  if (Array.isArray(a) ? a.some(function(x){return x<0||x>=o.length}) : !(a>=0&&a<o.length)) p.push(tag+': answer index out of range');
  if (!r[6]) p.push(tag+': no explanation');
  if (Array.isArray(ww) && ww.length!==o.length) p.push(tag+': whyWrong has '+ww.length+' entries for '+o.length+' options');
  if (Array.isArray(ww) && !Array.isArray(a) && ww[a]!=='') p.push(tag+': whyWrong text present for the correct option');
  if (Array.isArray(ww) && !Array.isArray(a)) ww.forEach(function(w,j){ if(j!==a && !w) p.push(tag+': no whyWrong for option '+j); });
  var key=String(r[3]).trim().toLowerCase(); if(seen[key]) p.push(tag+': same question as '+seen[key]); else seen[key]=tag;
 });
 /* answer position bias */
 var pos=[0,0,0,0,0,0]; LESSONS.forEach(function(l){(l.quiz||[]).forEach(function(q){ if(!Array.isArray(q.a)) pos[q.a]++; })});
 var pos2=[0,0,0,0,0,0]; NPQ.forEach(function(r){ if(!Array.isArray(r[5])) pos2[r[5]]++; });
 /* longest option is the answer */
 var longest=0,tot=0; LESSONS.forEach(function(l){(l.quiz||[]).forEach(function(q){ if(Array.isArray(q.a))return; tot++; var m=q.o.map(function(o){return String(o).length}); var mx=Math.max.apply(null,m); if(m[q.a]===mx && m.filter(function(x){return x===mx}).length===1) longest++; })});
 return JSON.stringify({problems:p, lessonAnswerPos:pos, bankAnswerPos:pos2, longestIsAnswer: longest+'/'+tot, total: LESSONS.reduce(function(a,l){return a+(l.quiz||[]).length},0)});
})()
'''
try:
    r = json.loads(c.js(JS))
    print('lesson quiz questions:', r['total'], 'answer position counts', r['lessonAnswerPos'], 'bank', r['bankAnswerPos'], 'longest option is the answer:', r['longestIsAnswer'])
    print(len(r['problems']), 'problems')
    for x in r['problems'][:80]: print(' ', x)
finally:
    proc.terminate()
