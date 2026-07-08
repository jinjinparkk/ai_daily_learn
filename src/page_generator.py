"""이중언어 학습 콘텐츠 dict → 날짜별 HTML 페이지."""
from __future__ import annotations

import html

from .templates import page_shell


def _e(s: str) -> str:
    return html.escape(str(s or ""))


def _bi(pair: dict) -> str:
    """영어 원문 + 한국어 번역 한 쌍."""
    if not pair:
        return ""
    return f"""<div class="bi">
  <div class="en"><span class="flag">EN</span><span>{_e(pair.get('en'))}</span></div>
  <div class="ko"><span class="flag">KO</span><span>{_e(pair.get('ko'))}</span></div>
</div>"""


def _bi_list(pairs: list[dict]) -> str:
    return f'<div class="biwrap">{"".join(_bi(p) for p in (pairs or []))}</div>'


def _terms(terms: list[dict]) -> str:
    if not terms:
        return ""
    rows = "".join(
        f'<div class="t"><span class="tt2">{_e(t.get("term"))}</span><span>{_e(t.get("meaning_ko"))}</span></div>'
        for t in terms
    )
    return f'<div class="terms">{rows}</div>'


def _fundamentals(f: dict) -> str:
    if not f:
        return ""
    return f"""<section class="block fund">
  <h2>오늘의 기초 · Fundamentals</h2>
  <div class="term">{_e(f.get('topic_ko'))} <span style="color:var(--muted);font-weight:600;font-size:16px">{_e(f.get('topic_en'))}</span></div>
  <div class="sublabel">이게 뭐야? · What is it</div>
  {_bi_list(f.get('what_it_is', []))}
  <div class="sublabel">작동 원리 · How it works</div>
  {_bi_list(f.get('how_it_works', []))}
  <div class="why"><strong>🧩 비유로 이해 · Analogy</strong>{_bi(f.get('analogy', {}))}</div>
  <div class="sublabel">기본 용어 · Key terms</div>
  {_terms(f.get('terms', []))}
</section>"""


def _key_concept(kc: dict) -> str:
    if not kc:
        return ""
    return f"""<section class="block concept">
  <h2>오늘의 핵심 개념 · Key Concept</h2>
  <div class="term">{_e(kc.get('term_ko'))} <span style="color:var(--muted);font-weight:600;font-size:16px">{_e(kc.get('term_en'))}</span></div>
  {_bi_list(kc.get('explanation', []))}
  <div class="why"><strong>왜 지금? · Why now</strong>{_bi(kc.get('why_now', {}))}</div>
</section>"""


def _papers(papers: list[dict]) -> str:
    if not papers:
        return ""
    rows = []
    for p in papers:
        diff = _e(p.get("difficulty", ""))
        rows.append(f"""<div class="paper">
  <div class="pt">{_e(p.get('title_ko'))}<span class="en">{_e(p.get('title_en'))}</span></div>
  <div><span class="pill d{diff}">{diff}</span></div>
  {_bi_list(p.get('summary', []))}
  <div class="why"><strong>💡 왜 중요한가</strong>{_bi(p.get('why_it_matters', {}))}</div>
  <div><a href="{_e(p.get('url'))}" target="_blank" rel="noopener">arXiv 원문 →</a></div>
</div>""")
    return f'<section class="block"><h2>주요 논문 해설 · Papers</h2>{"".join(rows)}</section>'


def _trends(trends: list[dict]) -> str:
    if not trends:
        return ""
    rows = []
    for t in trends:
        rows.append(f"""<div class="trend">
  <div class="tt"><a href="{_e(t.get('url'))}" target="_blank" rel="noopener">{_e(t.get('title_ko'))}</a></div>
  <div class="src">{_e(t.get('title_en'))} · {_e(t.get('source'))}</div>
  {_bi_list(t.get('insight', []))}
</div>""")
    return f'<section class="block"><h2>트렌드 인사이트 · Trends</h2>{"".join(rows)}</section>'


def _tools(tools: list[dict]) -> str:
    if not tools:
        return ""
    rows = []
    for t in tools:
        rows.append(f"""<div class="tool">
  <div class="tt"><a href="{_e(t.get('url'))}" target="_blank" rel="noopener">{_e(t.get('name'))}</a></div>
  {_bi(t.get('description', {}))}
</div>""")
    return f'<section class="block"><h2>주목할 오픈소스 · Tools</h2>{"".join(rows)}</section>'


def _quiz(quiz: list[dict]) -> str:
    if not quiz:
        return ""
    qs = []
    for q in quiz:
        opts = "".join(
            f'<button class="opt" type="button">{_e(o)}</button>' for o in q.get("options", [])
        )
        question = q.get("question", {})
        exp = q.get("explanation", {})
        qs.append(f"""<div class="q" data-answer="{int(q.get('answer_index', 0))}">
  <div class="qq">Q. {_e(question.get('ko'))}<br><span style="color:var(--muted);font-weight:400;font-size:13px">{_e(question.get('en'))}</span></div>
  {opts}
  <div class="exp">✅ {_e(exp.get('ko'))}<br><span style="color:#8a93a2">{_e(exp.get('en'))}</span></div>
</div>""")
    return f'<section class="block quiz"><h2>오늘의 퀴즈 · Quiz (클릭해서 정답 확인)</h2>{"".join(qs)}</section>'


def _vocab(vocab: list[dict]) -> str:
    if not vocab:
        return ""
    rows = []
    for v in vocab:
        rows.append(f"""<div class="v">
  <div class="vt">{_e(v.get('term'))}</div>
  <div class="vm">{_e(v.get('meaning_ko'))}</div>
  <div class="vex"><div class="e">“{_e(v.get('example_en'))}”</div><div class="k">{_e(v.get('example_ko'))}</div></div>
</div>""")
    return f'<section class="block vocab"><h2>핵심 영어 표현 · Vocabulary</h2>{"".join(rows)}</section>'


def _hero(date_str: str, data: dict, label: str) -> str:
    hl = data.get("headline", {})
    intro = _bi_list(data.get("intro", []))
    return f"""<div class="hero">
  <div class="date">{_e(date_str)}{label}</div>
  <div class="headline">{_e(hl.get('ko'))}</div>
  <div class="intro" style="color:#aab3c2;font-size:15px;margin-bottom:6px">{_e(hl.get('en'))}</div>
  {intro}
</div>"""


def _takeaway(data: dict) -> str:
    tk = data.get("takeaway", {})
    return f"""<div class="takeaway"><span class="lbl">오늘 반드시 기억할 것 · Takeaway</span>
  {_e(tk.get('ko'))}<br><span style="color:#9fe6c8;font-weight:400;font-size:14px">{_e(tk.get('en'))}</span></div>"""


def render_body(date_str: str, data: dict, label: str = "") -> str:
    """일일 학습 콘텐츠 본문 HTML (index/daily 공용)."""
    return f"""{_hero(date_str, data, label)}
{_fundamentals(data.get('fundamentals', {}))}
{_key_concept(data.get('key_concept', {}))}
{_papers(data.get('papers', []))}
{_trends(data.get('trends', []))}
{_tools(data.get('tools', []))}
{_quiz(data.get('quiz', []))}
{_vocab(data.get('vocab', []))}
{_takeaway(data)}"""


def render_daily(date_str: str, data: dict, brand: str, tagline: str) -> str:
    body = render_body(date_str, data)
    title = f"{date_str} · {brand}"
    return page_shell(title, body, tagline, brand, base="../", include_quiz_js=True)
