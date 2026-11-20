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
