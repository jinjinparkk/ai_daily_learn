"""학습 콘텐츠 dict → 날짜별 HTML 페이지."""
from __future__ import annotations

import html

from .templates import page_shell


def _e(s: str) -> str:
    return html.escape(str(s or ""))


def _key_concept(kc: dict) -> str:
    return f"""<section class="block concept">
  <h2>오늘의 핵심 개념</h2>
  <div class="term">{_e(kc.get('term'))}</div>
  <div>{_e(kc.get('explanation'))}</div>
  <div class="why"><strong>왜 지금?</strong> {_e(kc.get('why_now'))}</div>
</section>"""


def _papers(papers: list[dict]) -> str:
    if not papers:
        return ""
    rows = []
    for p in papers:
        diff = _e(p.get("difficulty", ""))
        rows.append(f"""<div class="paper">
  <div class="pt">{_e(p.get('title_ko'))}<span class="en">{_e(p.get('title'))}</span></div>
  <div><span class="pill d{diff}">{diff}</span></div>
  <div>{_e(p.get('summary'))}</div>
  <div class="why">💡 {_e(p.get('why_it_matters'))}</div>
  <div><a href="{_e(p.get('url'))}" target="_blank" rel="noopener">arXiv 원문 →</a></div>
</div>""")
    return f'<section class="block"><h2>주요 논문 해설</h2>{"".join(rows)}</section>'


def _trends(trends: list[dict]) -> str:
    if not trends:
        return ""
    rows = []
    for t in trends:
        rows.append(f"""<div class="trend">
  <div class="tt"><a href="{_e(t.get('url'))}" target="_blank" rel="noopener">{_e(t.get('title'))}</a></div>
  <div class="src">{_e(t.get('source'))}</div>
  <div>{_e(t.get('insight'))}</div>
</div>""")
    return f'<section class="block"><h2>트렌드 인사이트</h2>{"".join(rows)}</section>'


def _tools(tools: list[dict]) -> str:
    if not tools:
        return ""
    rows = []
    for t in tools:
        rows.append(f"""<div class="tool">
  <div class="tt"><a href="{_e(t.get('url'))}" target="_blank" rel="noopener">{_e(t.get('name'))}</a></div>
  <div>{_e(t.get('description'))}</div>
</div>""")
    return f'<section class="block"><h2>주목할 오픈소스 · 도구</h2>{"".join(rows)}</section>'


def _quiz(quiz: list[dict]) -> str:
    if not quiz:
        return ""
    qs = []
    for q in quiz:
        opts = "".join(
            f'<button class="opt" type="button">{_e(o)}</button>' for o in q.get("options", [])
        )
        qs.append(f"""<div class="q" data-answer="{int(q.get('answer_index', 0))}">
  <div class="qq">Q. {_e(q.get('question'))}</div>
  {opts}
  <div class="exp">✅ {_e(q.get('explanation'))}</div>
</div>""")
    return f'<section class="block quiz"><h2>오늘의 퀴즈 (클릭해서 정답 확인)</h2>{"".join(qs)}</section>'


def _glossary(gloss: list[dict]) -> str:
    if not gloss:
        return ""
    rows = "".join(
        f'<div class="g"><span class="gt">{_e(g.get("term"))}</span><span>{_e(g.get("definition"))}</span></div>'
        for g in gloss
    )
    return f'<section class="block"><h2>용어 사전</h2><div class="gloss">{rows}</div></section>'


def render_daily(date_str: str, data: dict, brand: str, tagline: str) -> str:
    """일일 학습 페이지 전체 HTML 반환."""
    body = f"""<div class="hero">
  <div class="date">{_e(date_str)}</div>
  <div class="headline">{_e(data.get('headline'))}</div>
  <div class="intro">{_e(data.get('intro'))}</div>
</div>
{_key_concept(data.get('key_concept', {}))}
{_papers(data.get('papers', []))}
{_trends(data.get('trends', []))}
{_tools(data.get('tools', []))}
{_quiz(data.get('quiz', []))}
{_glossary(data.get('glossary', []))}
<div class="takeaway"><span class="lbl">오늘 반드시 기억할 것</span>{_e(data.get('takeaway'))}</div>"""

    title = f"{date_str} · {brand}"
    return page_shell(title, body, tagline, brand, base="../", include_quiz_js=True)
