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
    # 분석 결과(learn json)를 커밋되는 위치에 보관 → Claude 재호출 없이 재렌더 가능
    content_dir: Path = field(default_factory=lambda: Path(os.getenv("AIDL_CONTENT_DIR", "content")))

    # --- 사이트 메타 ---
    site_title: str = field(default_factory=lambda: os.getenv("AIDL_SITE_TITLE", "AI Daily Learn"))
    site_tagline: str = field(
        default_factory=lambda: os.getenv("AIDL_SITE_TAGLINE", "매일 아침, AI가 나를 학습시킨다")
    )

    # --- 수집 파라미터 ---
    arxiv_categories: list[str] = field(
        default_factory=lambda: _split("AIDL_ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL,cs.CV")
    )
    arxiv_max_results: int = field(default_factory=lambda: int(os.getenv("AIDL_ARXIV_MAX", "40")))
    hf_limit: int = field(default_factory=lambda: int(os.getenv("AIDL_HF_LIMIT", "60")))
    # Claude 에 넘길 후보 논문 수 (여기서 4~6개를 선별). 중복 제거 후 이만큼 채운다.
    paper_pool: int = field(default_factory=lambda: int(os.getenv("AIDL_PAPER_POOL", "14")))
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


# 기초 커리큘럼 — 매일 하루에 하나씩 순환(날짜 기준)하며 원리+기본용어를 가르친다.
# 논문/트렌드와 독립적이라 기초가 체계적으로 쌓인다. 순서대로 약 한 달 주기.
FUNDAMENTALS: list[dict[str, str]] = [
    {"en": "Neural Network", "ko": "신경망"},
    {"en": "Gradient Descent", "ko": "경사하강법"},
    {"en": "Backpropagation", "ko": "역전파"},
    {"en": "Loss Function", "ko": "손실 함수"},
    {"en": "Activation Function", "ko": "활성화 함수"},
    {"en": "Overfitting & Regularization", "ko": "과적합과 정규화"},
    {"en": "Learning Rate", "ko": "학습률"},
    {"en": "Batch & Epoch", "ko": "배치와 에폭"},
    {"en": "Tokenization", "ko": "토큰화"},
    {"en": "Word Embeddings", "ko": "단어 임베딩"},
    {"en": "Attention Mechanism", "ko": "어텐션 메커니즘"},
    {"en": "Self-Attention", "ko": "셀프 어텐션"},
    {"en": "Transformer Architecture", "ko": "트랜스포머 구조"},
    {"en": "Softmax & Logits", "ko": "소프트맥스와 로짓"},
    {"en": "Pretraining vs Fine-tuning", "ko": "사전학습과 미세조정"},
    {"en": "Transfer Learning", "ko": "전이학습"},
    {"en": "In-Context Learning", "ko": "인컨텍스트 러닝"},
    {"en": "Prompt Engineering", "ko": "프롬프트 엔지니어링"},
    {"en": "Chain-of-Thought", "ko": "사고의 연쇄(CoT)"},
    {"en": "RLHF (Reinforcement Learning from Human Feedback)", "ko": "인간 피드백 기반 강화학습"},
    {"en": "Temperature & Sampling", "ko": "온도와 샘플링"},
    {"en": "Perplexity", "ko": "퍼플렉시티"},
    {"en": "Context Window", "ko": "컨텍스트 윈도우"},
    {"en": "Hallucination", "ko": "환각(할루시네이션)"},
    {"en": "RAG (Retrieval-Augmented Generation)", "ko": "검색 증강 생성"},
    {"en": "Vector Database & Similarity", "ko": "벡터 DB와 유사도"},
    {"en": "Quantization", "ko": "양자화"},
    {"en": "Mixture of Experts (MoE)", "ko": "전문가 혼합"},
    {"en": "Diffusion Models", "ko": "디퓨전 모델"},
    {"en": "LLM Agents & Tool Use", "ko": "LLM 에이전트와 도구 사용"},
    {"en": "Scaling Laws", "ko": "스케일링 법칙"},
    {"en": "Evaluation & Benchmarks", "ko": "평가와 벤치마크"},
]


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
