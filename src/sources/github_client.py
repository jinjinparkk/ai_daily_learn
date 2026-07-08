"""GitHub 검색 API 로 최근 인기 AI 오픈소스 레포 수집.

공식 'trending' API 는 없으므로, 최근 생성된 레포를 스타 순으로 정렬해 근사한다.
인증 없이도 동작하지만(분당 10회 제한), GITHUB_TOKEN 이 있으면 제한이 완화된다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

import requests

log = logging.getLogger("aidl.github")

_SEARCH = "https://api.github.com/search/repositories"


@dataclass
class Repo:
    name: str
    full_name: str
    description: str
    url: str
    stars: int
    language: str
    topic: str


def fetch_trending(topics: list[str], token: str = "", days_back: int = 30, per_topic: int = 3) -> list[Repo]:
    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    seen: set[str] = set()
    repos: list[Repo] = []
    for topic in topics:
        params = {
            "q": f"topic:{topic} created:>{since}",
            "sort": "stars",
            "order": "desc",
            "per_page": per_topic,
        }
        try:
            resp = requests.get(_SEARCH, headers=headers, params=params, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("GitHub 요청 실패 [%s]: %s", topic, exc)
            continue

        for item in resp.json().get("items", []):
            if item["full_name"] in seen:
                continue
            seen.add(item["full_name"])
            repos.append(
                Repo(
                    name=item.get("name", ""),
                    full_name=item.get("full_name", ""),
                    description=(item.get("description") or "").strip(),
                    url=item.get("html_url", ""),
                    stars=item.get("stargazers_count", 0),
                    language=item.get("language") or "",
                    topic=topic,
                )
            )
        log.info("GitHub [%s] 조회 완료", topic)

    repos.sort(key=lambda r: r.stars, reverse=True)
    log.info("GitHub 레포 %d건 수집", len(repos))
    return repos


def to_dicts(repos: list[Repo]) -> list[dict]:
    return [asdict(r) for r in repos]
