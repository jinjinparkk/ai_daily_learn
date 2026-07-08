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
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 미설치 시에도 동작
    pass

from . import analyzer, page_generator, site_builder
from .config import RSS_FEEDS, Config
from .sources import arxiv_client, github_client, rss_client


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _today(cfg: Config) -> str:
    return datetime.now(ZoneInfo(cfg.timezone)).strftime("%Y-%m-%d")


def collect(cfg: Config) -> dict:
    papers = arxiv_client.fetch_recent_papers(cfg.arxiv_categories, cfg.arxiv_max_results)
    news = rss_client.fetch_news(RSS_FEEDS)
    repos = github_client.fetch_trending(cfg.github_topics, cfg.github_token)
    return {
        "arxiv": arxiv_client.to_dicts(papers),
        "news": rss_client.to_dicts(news),
        "repos": github_client.to_dicts(repos),
    }


def run(cfg: Config, date_str: str, fetch_only: bool) -> int:
    log = logging.getLogger("aidl")
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    (cfg.site_dir / "daily").mkdir(parents=True, exist_ok=True)

    log.info("=== AI Daily Learn : %s ===", date_str)
    raw = collect(cfg)

    raw_path = cfg.data_dir / f"{date_str}_raw.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("원자료 저장: %s", raw_path)

    if fetch_only:
        log.info("--fetch-only: Claude 분석/페이지 생성 생략")
        return 0

    cfg.validate()
    data = analyzer.analyze(
        cfg.model, cfg.anthropic_api_key, date_str, raw["arxiv"], raw["news"], raw["repos"]
    )

    analysis_path = cfg.data_dir / f"{date_str}_learn.json"
    analysis_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

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
        site_builder.build_index(cfg.site_dir, date_str, data, cfg.site_title, cfg.site_tagline)
    else:
        # 과거 날짜를 재생성한 경우 index 는 최신 유지
        latest_data = json.loads(
            (cfg.data_dir / f"{latest['date']}_learn.json").read_text(encoding="utf-8")
        )
        site_builder.build_index(
            cfg.site_dir, latest["date"], latest_data, cfg.site_title, cfg.site_tagline
        )
    site_builder.build_archive(cfg.site_dir, manifest, cfg.site_title, cfg.site_tagline)

    log.info("=== 완료. 사이트: %s ===", cfg.site_dir.resolve())
    return 0


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(description="AI Daily Learn 파이프라인")
    parser.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    parser.add_argument("--fetch-only", action="store_true", help="수집만 하고 종료")
    args = parser.parse_args(argv)

    cfg = Config()
    date_str = args.date or _today(cfg)
    try:
        return run(cfg, date_str, args.fetch_only)
    except Exception:  # noqa: BLE001
        logging.getLogger("aidl").exception("파이프라인 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
