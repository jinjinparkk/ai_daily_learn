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
- 논문은 후보 중 가장 중요하고 흥미로운 4~6개를 선별한다 (전부 다루지 말 것).
  후보에는 upvotes(커뮤니티 추천수), keywords 가 있다 — 추천수가 높을수록 주목받는 논문이니
  선별과 순서에 참고하되, 오늘 학습으로서의 다양성과 가치도 함께 고려한다.
- 난이도(입문/중급/고급)를 정직하게 표기한다.
- vocab 은 오늘 실제 등장한 핵심 AI 영어 표현/용어를 뽑아, 뜻과 예문(영/한)을 함께 준다.
- 퀴즈는 오늘 콘텐츠 이해를 점검하는 문항으로 만든다.
- 과장하거나 근거 없는 단정을 피한다."""


# 출력 JSON 구조 명세 (structured-outputs 문법 컴파일 한계 회피 위해 프롬프트로 형태 지정)
# 주의: JSON 은 주석을 허용하지 않으므로 템플릿에 // 주석을 넣지 않는다.
_SHAPE = """반드시 아래 구조의 유효한 JSON 객체 '하나만' 출력하세요.
마크다운 코드펜스, 주석(//), 설명 문장 없이 순수 JSON 만 출력합니다.
모든 {"en","ko"} 는 서로 정확히 대응하는 영어/한국어 문장쌍입니다.

개수 가이드: intro 2~3, fundamentals.what_it_is 2~3, fundamentals.how_it_works 4~6,
fundamentals.terms 3~5, key_concept.explanation 4~6, papers 4~6, quiz 정확히 3, vocab 5~7.
difficulty 값은 "입문"/"중급"/"고급" 중 하나. answer_index 는 정답 보기의 0부터 시작하는 정수.

구조:
{
  "headline": {"en":"...","ko":"..."},
  "intro": [{"en":"...","ko":"..."}],
  "fundamentals": {
    "topic_en":"<배정된 주제 그대로>", "topic_ko":"<배정된 주제 그대로>",
    "what_it_is": [{"en":"...","ko":"..."}],
    "how_it_works": [{"en":"...","ko":"..."}],
    "analogy": {"en":"...","ko":"..."},
    "terms": [{"term":"...","meaning_ko":"..."}]
  },
  "key_concept": {"term_en":"...","term_ko":"...","explanation":[{"en":"...","ko":"..."}],"why_now":{"en":"...","ko":"..."}},
  "papers": [{"title_en":"...","title_ko":"...","summary":[{"en":"...","ko":"..."}],"why_it_matters":{"en":"...","ko":"..."},"difficulty":"입문","url":"..."}],
  "trends": [{"title_en":"...","title_ko":"...","insight":[{"en":"...","ko":"..."}],"source":"...","url":"..."}],
  "tools": [{"name":"...","description":{"en":"...","ko":"..."},"url":"..."}],
  "quiz": [{"question":{"en":"...","ko":"..."},"options":["...","...","...","..."],"answer_index":0,"explanation":{"en":"...","ko":"..."}}],
  "vocab": [{"term":"...","meaning_ko":"...","example_en":"...","example_ko":"..."}],
  "takeaway": {"en":"...","ko":"..."}
}"""


def _extract_json(text: str) -> str:
    """혹시 코드펜스나 앞뒤 설명이 섞여도 JSON 본문만 추출."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    start, end = t.find("{"), t.rfind("}")
    return t[start : end + 1] if start != -1 and end != -1 else t


def _repair_json(client: anthropic.Anthropic, model: str, broken: str) -> dict:
    """모델이 유효하지 않은 JSON을 낸 경우 한 번 교정 시도."""
    log.warning("JSON 파싱 실패 → Claude 로 교정 재시도")
    with client.messages.stream(
        model=model,
        max_tokens=24000,
        system="너는 JSON 교정기다. 입력을 구조와 내용은 그대로 둔 채 '유효한 JSON 객체 하나'로만 "
               "고쳐서 출력한다. 코드펜스, 주석, 설명 문장은 절대 넣지 않는다.",
        messages=[{"role": "user", "content": f"다음을 유효한 JSON 으로 고쳐줘:\n\n{broken}"}],
    ) as stream:
        fixed = stream.get_final_message()
    text = next((b.text for b in fixed.content if b.type == "text"), "")
    return json.loads(_extract_json(text))


def analyze(model: str, api_key: str, date_str: str, papers: list[dict], news: list[dict],
            repos: list[dict], fundamental: dict) -> dict:
    """원자료 → 이중언어 학습 콘텐츠 dict. Claude 호출 + JSON 파싱.

    fundamental: 오늘 배정된 기초 주제 {"en": ..., "ko": ...}.
    """
    client = anthropic.Anthropic(api_key=api_key)

    payload = {
        "date": date_str,
        "candidate_papers": papers,  # upvotes(추천수) 높은 순, 이미 다룬 논문은 제외됨
        "ai_news": news,
        "trending_repos": repos,
    }
    user_prompt = (
        f"오늘은 {date_str} 입니다. 아래는 지난 24시간 전후로 수집한 AI 원자료입니다.\n"
        f"이것을 이중언어(EN/KO) 학습 콘텐츠로 재구성해 주세요.\n\n"
        f"[오늘의 기초 주제 배정] fundamentals 섹션은 반드시 다음 주제로 작성하세요: "
        f"topic_en=\"{fundamental['en']}\", topic_ko=\"{fundamental['ko']}\".\n\n"
        f"{_SHAPE}\n\n"
        f"=== 원자료 ===\n"
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
    ) as stream:
        resp = stream.get_final_message()

    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        result = json.loads(_extract_json(text))
    except json.JSONDecodeError:
        result = _repair_json(client, model, text)
    log.info("Claude 분석 완료 (논문 %d / 퀴즈 %d / 어휘 %d)",
             len(result.get("papers", [])), len(result.get("quiz", [])), len(result.get("vocab", [])))
    return result
