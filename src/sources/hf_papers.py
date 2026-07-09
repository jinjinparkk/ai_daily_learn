"""Hugging Face Daily Papers 수집 — 커뮤니티 추천수(upvote) 기반 큐레이션.

arXiv '최신순'과 달리 '오늘 중요한 논문'을 추천수로 제공한다.
매일 목록이 바뀌므로 신선도+중요도를 동시에 확보. 인증 불필요.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict

import requests

log = logging.getLogger("aidl.hf")

_API = "https://huggingface.co/api/daily_papers"


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    summary: str
    url: str
    published: str
    upvotes: int
    keywords: list[str]


def fetch_daily_papers(limit: int = 60) -> list[Paper]:
    try:
        resp = requests.get(_API, params={"limit": limit}, timeout=25)
        resp.raise_for_status()
        items = resp.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("HF Daily Papers 요청 실패: %s", exc)
        return []

    papers: list[Paper] = []
    for item in items:
        p = item.get("paper", {}) or {}
        aid = p.get("id", "")
        if not aid:
            continue
        papers.append(
            Paper(
                arxiv_id=aid,
                title=(p.get("title") or item.get("title") or "").strip(),
                authors=[a.get("name", "") for a in (p.get("authors") or [])][:8],
                summary=(p.get("summary") or item.get("summary") or "").strip(),
                url=f"https://arxiv.org/abs/{aid}",
                published=item.get("publishedAt", p.get("publishedAt", "")),
                upvotes=int(p.get("upvotes", 0) or 0),
                keywords=list(p.get("ai_keywords") or [])[:6],
            )
        )
    # 추천수 내림차순 (중요도 순)
    papers.sort(key=lambda x: x.upvotes, reverse=True)
    log.info("HF Daily Papers %d건 수집 (최고 추천수 %d)",
             len(papers), papers[0].upvotes if papers else 0)
    return papers


def to_dicts(papers: list[Paper]) -> list[dict]:
    return [asdict(p) for p in papers]
