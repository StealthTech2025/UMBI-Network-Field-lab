import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
shim = r'''<script>
/* It persistence shim: keeps the app's localStorage values in It.store so progress survives closing the page.
   Each value is split into pieces whose stored (JSON, UTF-8) size stays under It's 32 KB per-value limit.
   A save writes a fresh generation of pieces (ls-<key>-<gen>-<i>) and only then moves the pointer (ls-<key>-p = "gen:count"),
   so a failed save leaves the previous copy readable. Old-format saves (ls-<key>-n / ls-<key>-<i>) are still read. */
(function(){
  var mem = {}, loaded = false, waiters = [], LIMIT = 30000, busy = {}, queued = {};
  var enc = window.TextEncoder ? new TextEncoder() : null;
  function size(s){ var j = JSON.stringify(s); return enc ? enc.encode(j).length : j.length * 3; }
  function base(k){ return ('ls-' + String(k).replace(/[^A-Za-z0-9_-]/g, '_')).slice(0, 54); }
  function pieces(v){
    var out = [], i = 0;
    while (i < v.length) {
      var len = Math.min(v.length - i, LIMIT), p;
      for (;;) {
        var end = i + len;
        if (end < v.length && /[\uD800-\uDBFF]/.test(v.charAt(end - 1))) end--; /* never split a surrogate pair */
        p = v.slice(i, end);
        var sz = size(p);
        if (sz <= LIMIT || len <= 1) break;
        len = Math.max(1, Math.floor(len * LIMIT / sz * 0.95));
      }
      out.push(p); i += p.length;
    }
    return out;
  }
  function readParts(prefix, n){
    var s = '';
    for (var i = 0; i < n; i++) { var p = It.store.get(prefix + i); if (typeof p !== 'string') return null; s += p; }
    return s;
  }
  function pointer(b){ var p = It.store.get(b + '-p'); var m = /^([01]):(\d+)$/.exec(p || ''); return m ? { g: +m[1], n: +m[2] } : null; }
  function readStore(k){
    var b = base(k), ptr = pointer(b);
    if (ptr) return readParts(b + '-' + ptr.g + '-', ptr.n);
    var n = It.store.get(b + '-n');                      /* old format */
    return typeof n === 'number' ? readParts(b + '-', n) : null;
  }
  function quiet(p){ return Promise.resolve(p).then(function(){ return true; }, function(){ return false; }); }
  function writeStore(k, v){
    var b = base(k), ptr = pointer(b), legacy = It.store.get(b + '-n');
    if (v == null) {
      var dels = [quiet(It.store.set(b + '-p', null))];
      return Promise.all(dels).then(function(){ cleanup(b, ptr, null, legacy); });
    }
    var parts = pieces(String(v));
    /* Small values (the progress record) get a fresh generation so a failed save never damages the saved copy.
       Big ones (exam review history, a live exam) are rewritten in place: two copies of them would not fit in It's 512 KB. */
    var inPlace = parts.length > 2, g = inPlace ? (ptr ? ptr.g : 0) : (ptr && ptr.g === 0 ? 1 : 0);
    return Promise.all(parts.map(function(p, i){ return quiet(It.store.set(b + '-' + g + '-' + i, p)); })).then(function(oks){
      if (oks.indexOf(false) >= 0) {                        /* keep the old copy; drop the half-written one; the next save tries again */
        if (!inPlace) parts.forEach(function(p, i){ quiet(It.store.set(b + '-' + g + '-' + i, null)); });
        return false;
      }
      return quiet(It.store.set(b + '-p', g + ':' + parts.length)).then(function(ok){
        if (ok) cleanup(b, ptr, { g: g, n: parts.length }, legacy);
        return ok;
      });
    });
  }
  function cleanup(b, oldPtr, newPtr, legacy){
    var other = newPtr ? 1 - newPtr.g : null;
    if (oldPtr && (!newPtr || oldPtr.g !== newPtr.g)) for (var i = 0; i < oldPtr.n; i++) quiet(It.store.set(b + '-' + oldPtr.g + '-' + i, null));
    if (other !== null) { var o = 0; while (It.store.get(b + '-' + other + '-' + o) !== undefined && o < 1000) { quiet(It.store.set(b + '-' + other + '-' + o, null)); o++; } }
    if (newPtr) { var j = newPtr.n; while (It.store.get(b + '-' + newPtr.g + '-' + j) !== undefined && j < newPtr.n + 1000) { quiet(It.store.set(b + '-' + newPtr.g + '-' + j, null)); j++; } }
    if (typeof legacy === 'number') { for (var x = 0; x < legacy; x++) quiet(It.store.set(b + '-' + x, null)); quiet(It.store.set(b + '-n', null)); }
  }
  /* one save per key at a time; while one runs, only the newest value waits */
  function save(k){
    if (busy[k]) { queued[k] = true; return; }
    busy[k] = true; queued[k] = false;
    var v = mem[k];
    Promise.resolve().then(function(){ return writeStore(k, v); }).catch(function(){}).then(function(){
      busy[k] = false; if (queued[k]) save(k);
    });
  }
  window.ITLS = {
    get: function(k){ if (!(k in mem)) { mem[k] = loaded ? readStore(k) : null; } return mem[k]; },
    set: function(k, v){ mem[k] = v == null ? null : String(v); if (loaded) save(k); },
    ready: function(fn){ if (loaded) fn(); else waiters.push(fn); }
  };
  function go(){ if (loaded) return; loaded = true; mem = {}; var w = waiters; waiters = []; w.forEach(function(f){ try { f(); } catch (e) { setTimeout(function(){ throw e; }); } }); }
  It.onState(function(){ go(); });
  setTimeout(go, 5000);
})();
</script>
'''
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (old, h.count(old))
    h = h.replace(old, new)
h = h.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + shim, 1)
rep("function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }",
    "function lsGet(k) { try { return window.ITLS.get(k); } catch (e) { return null; } }")
rep("function lsSet(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { } }",
    "function lsSet(k, v) { try { window.ITLS.set(k, v); } catch (e) { } }")
rep("try { localStorage.removeItem(LKEY); } catch (e) { }", "try { K.lsSet(LKEY, null); } catch (e) { }")
rep("    S.prog = readLocal() || blankProg();",
    "    instTok = lsGet(INSTMODE_KEY);\n    try { var c0 = JSON.parse(lsGet(CKEY)); if (c0) CLASS = c0; } catch (e) { }\n    S.prog = readLocal() || blankProg();")
rep("<script>if(window.NP_BOOT)window.NP_BOOT();</script>",
    "<script>window.ITLS.ready(function(){ if(window.NP_BOOT)window.NP_BOOT(); });</script>")
open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
