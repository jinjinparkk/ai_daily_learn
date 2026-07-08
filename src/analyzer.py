"""수집한 원자료를 Claude 로 '학습 콘텐츠'로 재구성.

단순 요약이 아니라 학습 흐름으로 구성한다:
핵심 개념 → 주요 논문 해설 → 트렌드 인사이트 → 도구 → 오늘의 퀴즈 → 용어사전.
"""
from __future__ import annotations

import json
import logging

import anthropic

log = logging.getLogger("aidl.analyzer")

# --- 학습 콘텐츠 스키마 (structured outputs) ---
LEARNING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string", "description": "오늘의 AI 흐름을 한 문장으로"},
        "intro": {"type": "string", "description": "오늘 학습을 여는 2~3문장 도입부"},
        "key_concept": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "term": {"type": "string"},
                "explanation": {"type": "string", "description": "비전공자도 이해할 수준으로 4~6문장"},
                "why_now": {"type": "string", "description": "왜 지금 이 개념이 중요한지"},
            },
            "required": ["term", "explanation", "why_now"],
        },
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "title_ko": {"type": "string", "description": "제목 한글 번역"},
                    "summary": {"type": "string", "description": "핵심 내용 3~4문장 한글 요약"},
                    "why_it_matters": {"type": "string", "description": "이 논문이 중요한 이유"},
                    "difficulty": {"type": "string", "enum": ["입문", "중급", "고급"]},
                    "url": {"type": "string"},
                },
                "required": ["title", "title_ko", "summary", "why_it_matters", "difficulty", "url"],
            },
        },
        "trends": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "insight": {"type": "string", "description": "뉴스가 시사하는 바 2~3문장"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["title", "insight", "source", "url"],
            },
        },
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "description": "무엇에 쓰는지 한글 1~2문장"},
                    "url": {"type": "string"},
                },
                "required": ["name", "description", "url"],
            },
        },
        "quiz": {
            "type": "array",
            "description": "오늘 학습 내용 기반 4지선다 퀴즈 3문항",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer_index": {"type": "integer", "description": "정답 보기의 0-based 인덱스"},
                    "explanation": {"type": "string", "description": "정답 해설"},
                },
                "required": ["question", "options", "answer_index", "explanation"],
            },
        },
        "glossary": {
            "type": "array",
            "description": "오늘 등장한 핵심 용어 3~5개",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "term": {"type": "string"},
                    "definition": {"type": "string", "description": "한 줄 정의"},
                },
                "required": ["term", "definition"],
            },
        },
        "takeaway": {"type": "string", "description": "오늘 반드시 기억할 한 가지"},
    },
    "required": [
        "headline",
        "intro",
        "key_concept",
        "papers",
        "trends",
        "tools",
        "quiz",
        "glossary",
        "takeaway",
    ],
}

_SYSTEM = """당신은 AI 분야를 가르치는 뛰어난 교육자입니다.
매일 수집된 arXiv 논문, AI 업계 뉴스, 오픈소스 트렌드를 바탕으로,
학습자(개발/기획 실무자)가 하루 10분이면 소화할 수 있는 한국어 학습 콘텐츠를 만듭니다.

원칙:
- 모든 결과물은 자연스러운 한국어로 작성 (전문 용어는 원어 병기).
- 단순 나열이 아니라 '왜 중요한가'를 설명해 학습이 되도록 한다.
- 논문은 가장 흥미롭고 영향력 있는 것 4~6개를 선별 (전부 다루지 말 것).
- 난이도(입문/중급/고급)를 정직하게 표기한다.
- 퀴즈는 오늘 콘텐츠를 실제로 이해했는지 점검하는 문항으로 만든다.
- 과장하지 말고, 근거 없는 단정을 피한다."""


def analyze(model: str, api_key: str, date_str: str, papers: list[dict], news: list[dict], repos: list[dict]) -> dict:
    """원자료 → 학습 콘텐츠 dict. Claude structured outputs 사용."""
    client = anthropic.Anthropic(api_key=api_key)

    payload = {
        "date": date_str,
        "arxiv_papers": papers,
        "ai_news": news,
        "trending_repos": repos,
    }
    user_prompt = (
        f"오늘은 {date_str} 입니다. 아래는 지난 24시간 전후로 수집한 AI 원자료입니다.\n"
        f"이것을 스키마에 맞는 학습 콘텐츠로 재구성해 주세요.\n\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
    )

    log.info("Claude 분석 시작 (model=%s, 논문 %d / 뉴스 %d / 레포 %d)",
             model, len(papers), len(news), len(repos))

    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
        output_config={"format": {"type": "json_schema", "schema": LEARNING_SCHEMA}},
    )

    text = next((b.text for b in resp.content if b.type == "text"), "")
    result = json.loads(text)
    log.info("Claude 분석 완료 (논문 %d / 퀴즈 %d)",
             len(result.get("papers", [])), len(result.get("quiz", [])))
    return result
