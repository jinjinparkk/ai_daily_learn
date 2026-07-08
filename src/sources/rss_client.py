"""AI 뉴스/블로그 RSS 피드 수집."""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

import feedparser

log = logging.getLogger("aidl.rss")


@dataclass
class NewsItem:
    source: str
    title: str
    summary: str
    url: str
    published: str


def fetch_news(feeds: list[dict[str, str]], days_back: int = 7, per_feed: int = 4) -> list[NewsItem]:
    """각 피드에서 최근 N일 이내 항목을 수집. 날짜 정보가 없으면 그냥 최신 순으로 포함."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    items: list[NewsItem] = []

    for feed_def in feeds:
        name, url = feed_def["name"], feed_def["url"]
        try:
            feed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001 - 개별 피드 실패는 전체를 막지 않음
            log.warning("RSS 파싱 실패 [%s]: %s", name, exc)
            continue

        count = 0
        for entry in feed.entries:
            if count >= per_feed:
                break
            published = _entry_datetime(entry)
            if published is not None and published < cutoff:
                continue
            items.append(
                NewsItem(
                    source=name,
                    title=_clean(entry.get("title", "")),
                    summary=_clean(entry.get("summary", ""))[:800],
                    url=entry.get("link", ""),
                    published=entry.get("published", entry.get("updated", "")),
                )
            )
            count += 1
        log.info("RSS [%s] %d건", name, count)

    log.info("RSS 총 %d건 수집", len(items))
    return items


def _entry_datetime(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _clean(text: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", text)  # HTML 태그 제거
    return " ".join(text.split()).strip()


def to_dicts(items: list[NewsItem]) -> list[dict]:
    return [asdict(i) for i in items]
