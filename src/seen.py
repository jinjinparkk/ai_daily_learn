"""이미 다룬 논문 추적 — 중복 방지.

arXiv ID 목록을 site/seen_papers.json 에 누적(커밋되어 CI 실행 간 유지).
버전 접미사(v1, v2)는 제거해 같은 논문을 동일 ID로 취급.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_MAX_KEEP = 800  # 무한정 증가 방지 (최근 것 위주 유지)
_ID_RE = re.compile(r"(\d{4}\.\d{4,5})")


def normalize_id(url_or_id: str) -> str:
    """URL 또는 ID 문자열에서 버전 없는 arXiv ID 추출. 실패 시 원본 소문자."""
    if not url_or_id:
        return ""
    m = _ID_RE.search(url_or_id)
    return m.group(1) if m else url_or_id.strip().lower()


def load_seen(site_dir: Path) -> set[str]:
    path = site_dir / "seen_papers.json"
    if path.exists():
        try:
            return set(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            return set()
    return set()


def save_seen(site_dir: Path, ids: set[str]) -> None:
    # set 은 순서가 없으므로 정렬해 저장(디프 안정 + 최근 유지 위해 뒤에서 자름)
    ordered = sorted(ids)[-_MAX_KEEP:]
    (site_dir / "seen_papers.json").write_text(
        json.dumps(ordered, ensure_ascii=False, indent=0), encoding="utf-8"
    )
