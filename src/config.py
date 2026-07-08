"""전역 설정 — 환경 변수(.env)에서 로드."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _split(env: str, default: str) -> list[str]:
    raw = os.getenv(env, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass
class Config:
    # --- Claude ---
    # 기본은 opus-4-8. 비용을 아끼려면 .env 에서 claude-haiku-4-5 또는 claude-sonnet-5 로 변경.
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("AIDL_MODEL", "claude-opus-4-8"))

    # --- 출력 경로 ---
    site_dir: Path = field(default_factory=lambda: Path(os.getenv("AIDL_SITE_DIR", "site")))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("AIDL_DATA_DIR", "data")))

    # --- 사이트 메타 ---
    site_title: str = field(default_factory=lambda: os.getenv("AIDL_SITE_TITLE", "AI Daily Learn"))
    site_tagline: str = field(
        default_factory=lambda: os.getenv("AIDL_SITE_TAGLINE", "매일 아침, AI가 나를 학습시킨다")
    )

    # --- 수집 파라미터 ---
    arxiv_categories: list[str] = field(
        default_factory=lambda: _split("AIDL_ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL,cs.CV")
    )
    arxiv_max_results: int = field(default_factory=lambda: int(os.getenv("AIDL_ARXIV_MAX", "30")))
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    github_topics: list[str] = field(
        default_factory=lambda: _split("AIDL_GITHUB_TOPICS", "llm,agent,rag,machine-learning")
    )

    # --- 시간대 ---
    timezone: str = field(default_factory=lambda: os.getenv("AIDL_TIMEZONE", "Asia/Seoul"))

    def validate(self) -> None:
        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY 가 설정되지 않았습니다. .env 파일을 확인하세요."
            )


# AI 뉴스/블로그 RSS 피드 — 스케줄 실행에서도 독립적으로 동작하는 안정 소스.
RSS_FEEDS: list[dict[str, str]] = [
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "The Berkeley AI Research (BAIR)", "url": "https://bair.berkeley.edu/blog/feed.xml"},
]
