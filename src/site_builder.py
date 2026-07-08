"""사이트 조립: manifest 관리, index.html(오늘), archive.html(지난 학습) 생성."""
from __future__ import annotations

import html
import json
import logging
from pathlib import Path

from .page_generator import render_body
from .templates import page_shell

log = logging.getLogger("aidl.site")


def _e(s: str) -> str:
    return html.escape(str(s or ""))


def load_manifest(site_dir: Path) -> list[dict]:
    path = site_dir / "manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_manifest(site_dir: Path, manifest: list[dict]) -> None:
    (site_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def upsert_manifest(site_dir: Path, date_str: str, headline_ko: str) -> list[dict]:
    manifest = load_manifest(site_dir)
    entry = {"date": date_str, "headline": headline_ko, "file": f"daily/{date_str}.html"}
    manifest = [m for m in manifest if m["date"] != date_str]
    manifest.append(entry)
    manifest.sort(key=lambda m: m["date"], reverse=True)
    save_manifest(site_dir, manifest)
    return manifest


def build_index(site_dir: Path, latest_date: str, data: dict, brand: str, tagline: str) -> None:
    """루트 index.html = 가장 최근 학습 콘텐츠(오늘)."""
    body = render_body(latest_date, data, label=" · 오늘의 학습 / Today")
    html_out = page_shell(brand, body, tagline, brand, base="", include_quiz_js=True)
    (site_dir / "index.html").write_text(html_out, encoding="utf-8")
    log.info("index.html 생성 (%s)", latest_date)


def build_archive(site_dir: Path, manifest: list[dict], brand: str, tagline: str) -> None:
    if manifest:
        items = "".join(
            f'<li><a href="{_e(m["file"])}"><span class="ad">{_e(m["date"])}</span>'
            f'<span class="ah">{_e(m["headline"])}</span></a></li>'
            for m in manifest
        )
        body = f'<div class="hero"><div class="headline">지난 학습 · Archive</div>' \
               f'<div class="intro">총 {len(manifest)}일의 학습 기록</div></div>' \
               f'<section class="block"><ul class="archive-list">{items}</ul></section>'
    else:
        body = '<div class="empty">아직 학습 기록이 없습니다.</div>'
    html_out = page_shell(f"지난 학습 · {brand}", body, tagline, brand, base="")
    (site_dir / "archive.html").write_text(html_out, encoding="utf-8")
    log.info("archive.html 생성 (%d일)", len(manifest))
