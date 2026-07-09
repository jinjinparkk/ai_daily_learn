"""파이프라인 진입점: 수집 → Claude 분석 → 페이지 생성 → 사이트 갱신.

사용:
  py -3 -m src                 # 오늘 날짜로 실행
  py -3 -m src --date 2026-07-08
  py -3 -m src --fetch-only    # 수집만 하고 data/ 에 저장 (Claude 호출 안 함)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 미설치 시에도 동작
    pass

from datetime import date as _date

from . import analyzer, page_generator, seen as seen_mod, site_builder
from .config import FUNDAMENTALS, RSS_FEEDS, Config
from .sources import arxiv_client, github_client, hf_papers, rss_client


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]{1,}")


def _collect_en_words(data: dict, cap: int = 800) -> list[str]:
    """콘텐츠에서 등장하는 영어 단어(소문자, 중복제거) 수집 — hover 사전 대상."""
    words: set[str] = set()

    def walk(o, key=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str) and key not in ("url", "ko", "meaning_ko", "example_ko",
                                                "topic_ko", "term_ko", "title_ko"):
            for w in _WORD_RE.findall(o):
                if len(w) >= 2:
                    words.add(w.lower())

    walk(data)
    return sorted(words)[:cap]


def _fundamental_for(date_str: str) -> dict:
    """날짜 기준으로 기초 커리큘럼을 결정적으로 순환 선택."""
    y, m, d = (int(x) for x in date_str.split("-"))
    idx = _date(y, m, d).toordinal() % len(FUNDAMENTALS)
    return FUNDAMENTALS[idx]


log = logging.getLogger("aidl")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _today(cfg: Config) -> str:
    return datetime.now(ZoneInfo(cfg.timezone)).strftime("%Y-%m-%d")


def _build_paper_pool(cfg: Config, seen: set[str], date_str: str) -> list[dict]:
    """중요도(HF 추천수) 우선 + arXiv 신선도 보충 + 이미 다룬 논문 제외."""
    pool: list[dict] = []
    used: set[str] = set()

    def add(title, authors, summary, url, upvotes, source, keywords):
        aid = seen_mod.normalize_id(url)
        if not aid or aid in seen or aid in used:
            return
        used.add(aid)
        pool.append({
            "title": title, "authors": authors, "summary": summary[:1200],
            "url": url, "upvotes": upvotes, "source": source, "keywords": keywords,
        })

    # 1) HF Daily Papers (해당 날짜의 중요도 순 큐레이션)
    for p in hf_papers.fetch_daily_papers(cfg.hf_limit, date=date_str):
        add(p.title, p.authors, p.summary, p.url, p.upvotes, "HuggingFace", p.keywords)

    # 2) 부족하면 arXiv 최신으로 보충
    if len(pool) < cfg.paper_pool:
        for p in arxiv_client.fetch_recent_papers(cfg.arxiv_categories, cfg.arxiv_max_results):
            if len(pool) >= cfg.paper_pool:
                break
            add(p.title, p.authors, p.summary, p.url, 0, "arXiv", [])

    log.info("논문 후보 %d건 (HF %d + arXiv 보충, 중복 %d건 제외됨)",
             len(pool), sum(1 for x in pool if x["source"] == "HuggingFace"), len(seen))
    return pool[: cfg.paper_pool]


def collect(cfg: Config, seen: set[str], date_str: str) -> dict:
    papers = _build_paper_pool(cfg, seen, date_str)
    news = rss_client.fetch_news(RSS_FEEDS)
    repos = github_client.fetch_trending(cfg.github_topics, cfg.github_token)
    return {
        "papers": papers,
        "news": rss_client.to_dicts(news),
        "repos": github_client.to_dicts(repos),
    }


def rerender(cfg: Config) -> int:
    """저장된 content/*.json 으로 모든 페이지를 다시 생성 (Claude 재호출 없음)."""
    files = sorted(cfg.content_dir.glob("*.json"))
    if not files:
        log.warning("재렌더할 content/*.json 이 없습니다.")
        return 1
    (cfg.site_dir / "daily").mkdir(parents=True, exist_ok=True)
    log.info("재렌더 시작: %d개 날짜", len(files))

    manifest: list[dict] = []
    latest_data = None
    for f in files:
        date_str = f.stem
        data = json.loads(f.read_text(encoding="utf-8"))
        # 손상 문자(U+FFFD) 정화 — 있으면 content 도 갱신
        clean = analyzer.sanitize(data)
        if clean != data:
            data = clean
            f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            log.info("[%s] 손상 문자 정화", date_str)
        # 워드북이 없으면 저가로 백필(키 있을 때만) 후 content 갱신
        if not data.get("wordbook") and cfg.anthropic_api_key:
            try:
                data["wordbook"] = analyzer.translate_words(
                    cfg.wordbook_model, cfg.anthropic_api_key, _collect_en_words(data))
                f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                log.info("[%s] 워드북 백필: %d단어", date_str, len(data["wordbook"]))
            except Exception:  # noqa: BLE001
                log.exception("[%s] 워드북 백필 실패(무시)", date_str)
        html = page_generator.render_daily(date_str, data, cfg.site_title, cfg.site_tagline)
        (cfg.site_dir / "daily" / f"{date_str}.html").write_text(html, encoding="utf-8")
        manifest = site_builder.upsert_manifest(
            cfg.site_dir, date_str, (data.get("headline") or {}).get("ko", ""))
        latest_data = (manifest[0]["date"], json.loads(
            (cfg.content_dir / f"{manifest[0]['date']}.json").read_text(encoding="utf-8")))

    if latest_data:
        site_builder.build_index(cfg.site_dir, latest_data[0], latest_data[1],
                                 cfg.site_title, cfg.site_tagline)
    site_builder.build_archive(cfg.site_dir, manifest, cfg.site_title, cfg.site_tagline)
    log.info("재렌더 완료: %d개 페이지", len(files))
    return 0


def run(cfg: Config, date_str: str, fetch_only: bool) -> int:
    log = logging.getLogger("aidl")
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    (cfg.site_dir / "daily").mkdir(parents=True, exist_ok=True)

    log.info("=== AI Daily Learn : %s ===", date_str)
    seen = seen_mod.load_seen(cfg.site_dir)
    raw = collect(cfg, seen, date_str)

    raw_path = cfg.data_dir / f"{date_str}_raw.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("원자료 저장: %s", raw_path)

    if fetch_only:
        log.info("--fetch-only: Claude 분석/페이지 생성 생략")
        return 0

    cfg.validate()
    fundamental = _fundamental_for(date_str)
    log.info("오늘의 기초 주제: %s / %s", fundamental["en"], fundamental["ko"])
    data = analyzer.analyze(
        cfg.model, cfg.anthropic_api_key, date_str,
        raw["papers"], raw["news"], raw["repos"], fundamental,
    )

    # 페이지 hover 사전(워드북) 생성 — 실패해도 무시(페이지는 정상)
    try:
        wb = analyzer.translate_words(cfg.wordbook_model, cfg.anthropic_api_key,
                                      _collect_en_words(data))
        data["wordbook"] = wb
        log.info("워드북 생성: %d단어", len(wb))
    except Exception:  # noqa: BLE001
        log.exception("워드북 생성 실패(무시)")
        data.setdefault("wordbook", {})

    analysis_path = cfg.data_dir / f"{date_str}_learn.json"
    analysis_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 커밋되는 위치에도 보관 → 나중에 템플릿만 바꿔 무료 재렌더 가능
    cfg.content_dir.mkdir(parents=True, exist_ok=True)
    (cfg.content_dir / f"{date_str}.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # 이번에 다룬 논문을 seen 에 기록 → 다음 실행부터 중복 제외
    for p in data.get("papers", []):
        aid = seen_mod.normalize_id(p.get("url", ""))
        if aid:
            seen.add(aid)
    seen_mod.save_seen(cfg.site_dir, seen)
    log.info("중복추적 갱신: 누적 %d편", len(seen))

    # 날짜별 페이지
    daily_html = page_generator.render_daily(date_str, data, cfg.site_title, cfg.site_tagline)
    daily_file = cfg.site_dir / "daily" / f"{date_str}.html"
    daily_file.write_text(daily_html, encoding="utf-8")
    log.info("일일 페이지 생성: %s", daily_file)

    # 인덱스 + 아카이브
    headline_ko = (data.get("headline") or {}).get("ko", "")
    manifest = site_builder.upsert_manifest(cfg.site_dir, date_str, headline_ko)
    latest = manifest[0]
    if latest["date"] == date_str:
        # 오늘(최신)을 생성한 경우에만 index(오늘) 갱신
        site_builder.build_index(cfg.site_dir, date_str, data, cfg.site_title, cfg.site_tagline)
    else:
        # 과거 날짜 재생성 시 index 는 건드리지 않음 (최신 날짜가 index 를 담당)
        log.info("과거 날짜(%s) 생성 — index 는 최신(%s) 유지, 갱신 생략", date_str, latest["date"])
    site_builder.build_archive(cfg.site_dir, manifest, cfg.site_title, cfg.site_tagline)

    log.info("=== 완료. 사이트: %s ===", cfg.site_dir.resolve())
    return 0


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(description="AI Daily Learn 파이프라인")
    parser.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    parser.add_argument("--fetch-only", action="store_true", help="수집만 하고 종료")
    parser.add_argument("--rerender", action="store_true",
                        help="저장된 content 로 페이지만 다시 생성 (Claude 호출 없음)")
    args = parser.parse_args(argv)

    cfg = Config()
    date_str = args.date or _today(cfg)
    try:
        if args.rerender:
            return rerender(cfg)
        return run(cfg, date_str, args.fetch_only)
    except Exception:  # noqa: BLE001
        logging.getLogger("aidl").exception("파이프라인 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
