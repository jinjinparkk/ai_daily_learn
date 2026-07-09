"""공유 HTML 셸과 CSS. 외부 의존성 없는 자체 완결 정적 페이지."""
from __future__ import annotations

CSS = """
:root{
  --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --line:#2a2f3a;
  --text:#e6e8ec; --muted:#9aa4b2; --accent:#7c9cff; --accent2:#5ee6b5;
  --warn:#ffc15e; --pill:#242938;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:860px;margin:0 auto;padding:0 20px 80px}
header.top{border-bottom:1px solid var(--line);padding:22px 0;margin-bottom:8px}
header.top .wrap{padding-bottom:0}
.brand{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.brand h1{font-size:20px;margin:0}
.brand .tag{color:var(--muted);font-size:14px}
nav.top{margin-top:10px;display:flex;gap:16px;font-size:14px}
.hero{padding:36px 0 8px}
.date{color:var(--accent2);font-weight:600;letter-spacing:.02em;font-size:14px}
.headline{font-size:30px;line-height:1.35;margin:10px 0 6px;font-weight:800}
.intro{color:var(--muted);font-size:16px}
section.block{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:22px 24px;margin:22px 0}
section.block h2{font-size:15px;margin:0 0 14px;color:var(--accent);letter-spacing:.06em;
  text-transform:uppercase;font-weight:700}
.concept .term,.fund .term{font-size:22px;font-weight:800;margin:0 0 8px}
.fund .sublabel{color:var(--accent2);font-size:12px;font-weight:700;letter-spacing:.04em;
  text-transform:uppercase;margin:14px 0 4px}
.terms{display:grid;gap:7px;margin-top:6px}
.terms .t{display:flex;gap:10px;font-size:14px;align-items:baseline}
.terms .tt2{color:var(--accent);font-weight:700;min-width:180px;flex:0 0 auto}
.fund{border-left:3px solid var(--accent2)}
.concept .why,.fund .why{margin-top:12px;padding:12px 14px;background:var(--panel2);border-radius:10px;
  border-left:3px solid var(--accent2);color:var(--muted);font-size:14px}
.concept .why .bi,.fund .why .bi,.paper .why .bi{border-bottom:none;padding:4px 0}
/* 이중언어 문장쌍 */
.bi{padding:9px 0;border-bottom:1px dashed var(--line)}
.bi:last-child{border-bottom:none}
.bi .en,.bi .ko{display:flex;gap:9px;align-items:flex-start;font-size:15px;line-height:1.6}
.bi .en{color:#aab3c2}
.bi .ko{color:var(--text);margin-top:4px}
.bi .flag{flex:0 0 auto;font-size:10px;font-weight:800;letter-spacing:.03em;color:var(--accent);
  padding:2px 6px;background:var(--pill);border-radius:5px;margin-top:3px}
.bi .en .flag{color:var(--accent)} .bi .ko .flag{color:var(--accent2)}
.biwrap{margin:6px 0}
/* 용어 툴팁: 영어 단어에 hover/tap → 뜻 표시 */
.tip{border-bottom:1px dotted var(--accent);cursor:help;position:relative;outline:none}
.tip::after{content:attr(data-tip);position:absolute;left:0;bottom:135%;
  background:#0b0d12;color:var(--text);border:1px solid var(--accent);
  padding:6px 10px;border-radius:7px;font-size:13px;line-height:1.5;font-weight:400;
  width:max-content;max-width:280px;white-space:normal;
  box-shadow:0 6px 18px rgba(0,0,0,.45);
  opacity:0;visibility:hidden;transform:translateY(4px);transition:.12s;
  pointer-events:none;z-index:20}
.tip:hover::after,.tip:focus::after{opacity:1;visibility:visible;transform:translateY(0)}
/* 일반 영어 단어 hover 사전 */
.w{border-radius:3px;transition:background .1s}
.w:hover{background:rgba(124,156,255,.20);cursor:help}
.wtip{position:absolute;background:#0b0d12;color:var(--text);border:1px solid var(--accent);
  padding:5px 10px;border-radius:7px;font-size:13px;line-height:1.5;max-width:280px;
  box-shadow:0 6px 18px rgba(0,0,0,.5);opacity:0;visibility:hidden;transition:.1s;
  z-index:40;pointer-events:none}
.wtip.show{opacity:1;visibility:visible}
.wtip b{color:var(--accent2)}
.paper{padding:16px 0;border-bottom:1px solid var(--line)}
.paper:last-child{border-bottom:none;padding-bottom:0}
.paper .pt{font-weight:700;font-size:16px}
.paper .pt .en{display:block;color:var(--muted);font-weight:400;font-size:13px;margin-top:2px}
.paper .why{color:var(--accent2);font-size:14px;margin-top:6px}
.pill{display:inline-block;background:var(--pill);color:var(--muted);font-size:12px;
  padding:2px 9px;border-radius:999px;margin-right:6px}
.pill.d입문{color:var(--accent2)} .pill.d중급{color:var(--warn)} .pill.d고급{color:#ff8f8f}
.trend,.tool{padding:12px 0;border-bottom:1px solid var(--line)}
.trend:last-child,.tool:last-child{border-bottom:none}
.trend .tt,.tool .tt{font-weight:700}
.trend .src{color:var(--muted);font-size:12px}
.quiz .q{margin:0 0 20px;padding-bottom:16px;border-bottom:1px solid var(--line)}
.quiz .q:last-child{border-bottom:none;margin-bottom:0}
.quiz .qq{font-weight:700;margin-bottom:10px}
.quiz .opt{display:block;width:100%;text-align:left;background:var(--panel2);color:var(--text);
  border:1px solid var(--line);border-radius:9px;padding:10px 14px;margin:6px 0;cursor:pointer;
  font-size:14px;transition:.15s}
.quiz .opt:hover{border-color:var(--accent)}
.quiz .opt.correct{border-color:var(--accent2);background:#16352b}
.quiz .opt.wrong{border-color:#ff8f8f;background:#3a1e1e}
.quiz .exp{display:none;margin-top:8px;padding:10px 12px;background:var(--panel2);
  border-radius:8px;color:var(--muted);font-size:14px}
/* 핵심 영어 표현 (어휘) */
.vocab .v{padding:12px 0;border-bottom:1px solid var(--line)}
.vocab .v:last-child{border-bottom:none}
.vocab .vt{font-weight:800;font-size:16px;color:var(--accent)}
.vocab .vm{color:var(--text);font-size:14px;margin-top:1px}
.vocab .vex{margin-top:6px;padding:8px 12px;background:var(--panel2);border-radius:8px;font-size:13px}
.vocab .vex .e{color:#aab3c2} .vocab .vex .k{color:var(--muted);margin-top:2px}
.takeaway{background:linear-gradient(135deg,#1b2740,#16352b);border:1px solid var(--line);
  border-radius:14px;padding:20px 24px;margin:26px 0;font-size:17px;font-weight:600}
.takeaway .lbl{display:block;color:var(--accent2);font-size:12px;letter-spacing:.08em;
  text-transform:uppercase;margin-bottom:6px}
footer{color:var(--muted);font-size:13px;text-align:center;padding:30px 0;border-top:1px solid var(--line)}
.archive-list{list-style:none;padding:0;margin:0}
.archive-list li{border-bottom:1px solid var(--line);padding:14px 0}
.archive-list li:last-child{border-bottom:none}
.archive-list .ad{color:var(--accent2);font-size:13px;font-weight:600}
.archive-list .ah{display:block;font-size:16px;margin-top:2px}
.empty{color:var(--muted);padding:40px 0;text-align:center}
"""

QUIZ_JS = """
document.querySelectorAll('.quiz .opt').forEach(function(btn){
  btn.addEventListener('click',function(){
    var q=btn.closest('.q');
    if(q.dataset.done)return;
    q.dataset.done='1';
    var ans=parseInt(q.dataset.answer,10);
    q.querySelectorAll('.opt').forEach(function(o,i){
      if(i===ans)o.classList.add('correct');
      else if(o===btn)o.classList.add('wrong');
      o.style.cursor='default';
    });
    var exp=q.querySelector('.exp'); if(exp)exp.style.display='block';
  });
});
"""


# 본문 영어 단어에 hover → 워드북(window.__WB__)에서 뜻 조회. 활용형(복수/과거/-ing 등)도 처리.
DICT_HOVER_JS = r"""
(function(){
  var WB = window.__WB__ || {};
  if (!Object.keys(WB).length) return;
  var SEL = '.bi .en, .vocab .vex .e, .paper .pt .en, .concept .term, .fund .term';

  function wrapWords(root){
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var nodes = [];
    while (walker.nextNode()){
      var n = walker.currentNode;
      if (n.parentNode.closest('.tip, .flag, .w')) continue;   // 핵심용어/뱃지/이미처리 제외
      if (!/[A-Za-z]/.test(n.nodeValue)) continue;
      nodes.push(n);
    }
    nodes.forEach(function(n){
      var frag = document.createDocumentFragment();
      n.nodeValue.split(/(\b[A-Za-z][A-Za-z'\-]*\b)/).forEach(function(p){
        if (/^[A-Za-z][A-Za-z'\-]*$/.test(p)){
          var s = document.createElement('span'); s.className='w'; s.textContent=p; frag.appendChild(s);
        } else { frag.appendChild(document.createTextNode(p)); }
      });
      n.parentNode.replaceChild(frag, n);
    });
  }
  document.querySelectorAll(SEL).forEach(wrapWords);

  function lookup(w){
    w = w.toLowerCase();
    if (WB[w]) return WB[w];
    var c = [];
    if (w.length > 3){
      if (w.slice(-3)==='ies') c.push(w.slice(0,-3)+'y');
      if (w.slice(-2)==='es') c.push(w.slice(0,-2));
      if (w.slice(-1)==='s') c.push(w.slice(0,-1));
      if (w.slice(-2)==='ed'){ c.push(w.slice(0,-2)); c.push(w.slice(0,-1)); }
      if (w.slice(-3)==='ing'){ c.push(w.slice(0,-3)); c.push(w.slice(0,-3)+'e'); }
      if (w.slice(-2)==='ly') c.push(w.slice(0,-2));
    }
    for (var i=0;i<c.length;i++) if (WB[c[i]]) return WB[c[i]];
    return null;
  }

  var tip = document.createElement('div'); tip.className='wtip'; document.body.appendChild(tip);
  document.addEventListener('mouseover', function(e){
    var t = e.target;
    if (!t.classList || !t.classList.contains('w')) return;
    var m = lookup(t.textContent);
    if (!m){ tip.classList.remove('show'); return; }
    tip.innerHTML = '<b>'+t.textContent+'</b> — ' + m;
    tip.classList.add('show');
    var r = t.getBoundingClientRect();
    var top = window.scrollY + r.top - tip.offsetHeight - 8;
    if (top < window.scrollY + 4) top = window.scrollY + r.bottom + 8;  // 위 공간 없으면 아래로
    var left = Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - tip.offsetWidth - 8);
    tip.style.top = top + 'px'; tip.style.left = Math.max(4, left) + 'px';
  });
  document.addEventListener('mouseout', function(e){
    if (e.target.classList && e.target.classList.contains('w')) tip.classList.remove('show');
  });
})();
"""


def page_shell(title: str, body: str, tagline: str, brand: str, base: str = "",
               include_quiz_js: bool = False, wordbook_json: str = "") -> str:
    """base: 루트까지의 상대 경로 접두사. 루트 페이지는 "", /daily/ 하위는 "../"."""
    js = f"<script>{QUIZ_JS}</script>" if include_quiz_js else ""
    if wordbook_json and wordbook_json != "{}":
        js += f"<script>window.__WB__={wordbook_json};{DICT_HOVER_JS}</script>"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="brand"><h1><a href="{base}index.html">{brand}</a></h1><span class="tag">{tagline}</span></div>
  <nav class="top"><a href="{base}index.html">오늘</a><a href="{base}archive.html">지난 학습</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer>{brand} · Claude 가 매일 자동 생성 · 학습은 복리입니다 📈</footer>
{js}
</body>
</html>"""
