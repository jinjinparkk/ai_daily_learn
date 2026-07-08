"""arXiv API 로 최신 AI 논문 수집.

공개 Atom API (http://export.arxiv.org/api/query) 사용 — 인증 불필요, 안정적.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict

import feedparser

log = logging.getLogger("aidl.arxiv")

_API = "http://export.arxiv.org/api/query"


@dataclass
class Paper:
    title: str
    authors: list[str]
    summary: str
    url: str
    published: str
    categories: list[str]


def fetch_recent_papers(categories: list[str], max_results: int = 30) -> list[Paper]:
    """지정 카테고리에서 최근 제출된 논문을 제출일 내림차순으로 수집."""
    cat_query = "+OR+".join(f"cat:{c}" for c in categories)
    query = (
        f"{_API}?search_query={cat_query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&start=0&max_results={max_results}"
    )
    log.info("arXiv 요청: %s (max=%d)", ",".join(categories), max_results)

    feed = _parse_with_retry(query)
    papers: list[Paper] = []
    for entry in feed.entries:
        papers.append(
            Paper(
                title=_clean(entry.get("title", "")),
                authors=[a.get("name", "") for a in entry.get("authors", [])],
                summary=_clean(entry.get("summary", "")),
                url=entry.get("link", ""),
                published=entry.get("published", ""),
                categories=[t.get("term", "") for t in entry.get("tags", [])],
            )
        )
    log.info("arXiv 논문 %d건 수집", len(papers))
    return papers


def _parse_with_retry(url: str, retries: int = 3):
    last = None
    for attempt in range(retries):
        feed = feedparser.parse(url)
        if feed.entries:
            return feed
        last = feed
        log.warning("arXiv 응답 비어있음 (시도 %d/%d), 재시도", attempt + 1, retries)
        time.sleep(3)
    return last if last is not None else feedparser.parse(url)


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def to_dicts(papers: list[Paper]) -> list[dict]:
    return [asdict(p) for p in papers]
