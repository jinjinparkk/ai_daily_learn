"""수집한 원자료를 Claude 로 이중언어(EN/KO) '학습 콘텐츠'로 재구성.

팀원들이 AI 지식과 영어를 함께 학습할 수 있도록,
모든 서술형 콘텐츠를 영어 원문 + 한국어 번역 문장쌍으로 생성한다.
구성: 핵심 개념 → 주요 논문 해설 → 트렌드 인사이트 → 도구 → 퀴즈 → 핵심 영어 표현.
"""
from __future__ import annotations

import json
import logging

import anthropic

log = logging.getLogger("aidl.analyzer")

# 영어 원문 + 한국어 번역 문장쌍
_BI = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "en": {"type": "string", "description": "영어 원문 (한 문장)"},
        "ko": {"type": "string", "description": "자연스러운 한국어 번역"},
    },
    "required": ["en", "ko"],
}


def _bi_list(desc: str) -> dict:
    return {"type": "array", "description": desc, "items": _BI}


# --- 이중언어 학습 콘텐츠 스키마 (structured outputs) ---
LEARNING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {**_BI, "description": "오늘의 AI 흐름을 한 문장으로 (EN/KO)"},
        "intro": _bi_list("오늘 학습을 여는 도입부 2~3개 문장쌍"),
        "fundamentals": {
            "type": "object",
            "description": "오늘 배정된 '기초 개념'을 원리부터 가르치는 섹션",
            "additionalProperties": False,
            "properties": {
                "topic_en": {"type": "string", "description": "배정된 기초 주제(영어) 그대로"},
                "topic_ko": {"type": "string", "description": "배정된 기초 주제(한국어) 그대로"},
                "what_it_is": _bi_list("이게 무엇인지 2~3개 문장쌍 (입문자용)"),
                "how_it_works": _bi_list("작동 원리를 단계적으로 4~6개 문장쌍"),
                "analogy": {**_BI, "description": "일상적 비유로 이해시키기 (EN/KO)"},
                "terms": {
                    "type": "array",
                    "description": "이 주제의 기본 용어 3~5개",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "term": {"type": "string", "description": "용어(영어, 약어면 풀네임)"},
                            "meaning_ko": {"type": "string", "description": "한국어 정의 한 줄"},
                        },
                        "required": ["term", "meaning_ko"],
                    },
                },
            },
            "required": ["topic_en", "topic_ko", "what_it_is", "how_it_works", "analogy", "terms"],
        },
        "key_concept": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "term_en": {"type": "string"},
                "term_ko": {"type": "string"},
                "explanation": _bi_list("비전공자도 이해할 개념 설명 4~6개 문장쌍"),
                "why_now": {**_BI, "description": "왜 지금 중요한지 (EN/KO)"},
            },
            "required": ["term_en", "term_ko", "explanation", "why_now"],
        },
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title_en": {"type": "string", "description": "논문 영어 제목"},
                    "title_ko": {"type": "string", "description": "제목 한글 번역"},
                    "summary": _bi_list("핵심 내용 3~4개 문장쌍"),
                    "why_it_matters": {**_BI, "description": "중요한 이유 (EN/KO)"},
                    "difficulty": {"type": "string", "enum": ["입문", "중급", "고급"]},
                    "url": {"type": "string"},
                },
                "required": ["title_en", "title_ko", "summary", "why_it_matters", "difficulty", "url"],
            },
        },
        "trends": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title_en": {"type": "string"},
                    "title_ko": {"type": "string"},
                    "insight": _bi_list("시사점 2~3개 문장쌍"),
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["title_en", "title_ko", "insight", "source", "url"],
            },
        },
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "description": {**_BI, "description": "무엇에 쓰는지 (EN/KO)"},
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
                    "question": {**_BI, "description": "문제 (EN/KO)"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "보기(한국어)"},
                    "answer_index": {"type": "integer", "description": "정답 보기의 0-based 인덱스"},
                    "explanation": {**_BI, "description": "정답 해설 (EN/KO)"},
                },
                "required": ["question", "options", "answer_index", "explanation"],
            },
        },
        "vocab": {
            "type": "array",
            "description": "오늘 콘텐츠에서 뽑은 핵심 AI 영어 표현/용어 5~7개",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "term": {"type": "string", "description": "영어 표현/용어 (약어면 풀네임 병기)"},
                    "meaning_ko": {"type": "string", "description": "한국어 뜻"},
                    "example_en": {"type": "string", "description": "이 표현을 쓴 예문 (영어)"},
                    "example_ko": {"type": "string", "description": "예문 번역"},
                },
                "required": ["term", "meaning_ko", "example_en", "example_ko"],
            },
        },
        "takeaway": {**_BI, "description": "오늘 반드시 기억할 한 가지 (EN/KO)"},
    },
    "required": [
        "headline",
        "intro",
        "fundamentals",
        "key_concept",
        "papers",
        "trends",
        "tools",
        "quiz",
        "vocab",
        "takeaway",
    ],
}

_SYSTEM = """당신은 AI 분야를 가르치는 뛰어난 이중언어(영어/한국어) 교육자입니다.
매일 수집된 arXiv 논문, AI 업계 뉴스, 오픈소스 트렌드를 바탕으로,
팀원들이 'AI 지식'과 '영어'를 동시에 학습할 수 있는 콘텐츠를 만듭니다.

핵심 원칙 — 이중언어:
- 모든 서술형 콘텐츠는 영어 원문(en)과 자연스러운 한국어 번역(ko)을 문장쌍으로 제공한다.
- 영어는 원어민이 쓰는 명확하고 학습에 좋은 문장으로 작성한다 (너무 어렵지도, 유치하지도 않게).
- 한국어는 직역이 아니라 뜻이 잘 통하는 자연스러운 번역으로 작성한다.
- 각 en 문장과 ko 문장은 서로 정확히 대응해야 한다 (한 문장 = 한 쌍).

내용 원칙:
- fundamentals(오늘의 기초): 배정된 기초 주제를 '원리부터' 처음 배우는 사람도 이해하도록 가르친다.
  topic_en/topic_ko 는 배정된 주제를 그대로 쓰고, 작동 원리(how_it_works)와 비유(analogy),
  기본 용어(terms)를 충실히 채운다. 이 섹션은 그날 논문과 무관하게 독립적인 기초 강의다.
- 논문은 가장 흥미롭고 영향력 있는 것 4~6개를 선별한다 (전부 다루지 말 것).
- 난이도(입문/중급/고급)를 정직하게 표기한다.
- vocab 은 오늘 실제 등장한 핵심 AI 영어 표현/용어를 뽑아, 뜻과 예문(영/한)을 함께 준다.
- 퀴즈는 오늘 콘텐츠 이해를 점검하는 문항으로 만든다.
- 과장하거나 근거 없는 단정을 피한다."""


def analyze(model: str, api_key: str, date_str: str, papers: list[dict], news: list[dict],
            repos: list[dict], fundamental: dict) -> dict:
    """원자료 → 이중언어 학습 콘텐츠 dict. Claude structured outputs + streaming.

    fundamental: 오늘 배정된 기초 주제 {"en": ..., "ko": ...}.
    """
    client = anthropic.Anthropic(api_key=api_key)

    payload = {
        "date": date_str,
        "arxiv_papers": papers,
        "ai_news": news,
        "trending_repos": repos,
    }
    user_prompt = (
        f"오늘은 {date_str} 입니다. 아래는 지난 24시간 전후로 수집한 AI 원자료입니다.\n"
        f"이것을 스키마에 맞는 이중언어(EN/KO) 학습 콘텐츠로 재구성해 주세요.\n\n"
        f"[오늘의 기초 주제 배정] fundamentals 섹션은 반드시 다음 주제로 작성하세요: "
        f"topic_en=\"{fundamental['en']}\", topic_ko=\"{fundamental['ko']}\".\n\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
    )

    log.info("Claude 분석 시작 (model=%s, 논문 %d / 뉴스 %d / 레포 %d)",
             model, len(papers), len(news), len(repos))

    # 이중언어라 출력이 커서 streaming 사용 (HTTP 타임아웃 방지)
    with client.messages.stream(
        model=model,
        max_tokens=24000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
        output_config={"format": {"type": "json_schema", "schema": LEARNING_SCHEMA}},
    ) as stream:
        resp = stream.get_final_message()

    text = next((b.text for b in resp.content if b.type == "text"), "")
    result = json.loads(text)
    log.info("Claude 분석 완료 (논문 %d / 퀴즈 %d / 어휘 %d)",
             len(result.get("papers", [])), len(result.get("quiz", [])), len(result.get("vocab", [])))
    return result
