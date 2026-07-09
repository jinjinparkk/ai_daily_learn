# AI Daily Learn

**매일 아침 자동으로 새 페이지가 생성되는 AI 학습 웹사이트.**

**중요 논문(HuggingFace Daily Papers, 추천수 큐레이션)** + AI 업계 뉴스(RSS) + GitHub 트렌드를 수집하고,
이미 다룬 논문은 자동 제외(중복 방지)한 뒤,
Claude 가 이를 **단순 요약이 아닌 학습 콘텐츠**로 재구성합니다:

> 핵심 개념 → 주요 논문 해설 → 트렌드 인사이트 → 주목할 도구 → 오늘의 퀴즈 → 용어사전

결과물은 날짜별 정적 HTML 페이지(`site/daily/YYYY-MM-DD.html`)로 쌓이고,
`index.html`(오늘)과 `archive.html`(지난 학습)이 자동 갱신됩니다.

## 구조

```
ai_daily_learn/
├─ src/
│  ├─ __main__.py        # 파이프라인 진입점
│  ├─ config.py          # 설정 + RSS 피드 목록
│  ├─ analyzer.py        # Claude 분석 (structured outputs)
│  ├─ page_generator.py  # 일일 HTML 렌더링
│  ├─ site_builder.py    # index/archive/manifest
│  ├─ templates.py       # 공유 셸 + CSS + 퀴즈 JS
│  ├─ seen.py            # 이미 다룬 논문 추적(중복 방지)
│  └─ sources/
│     ├─ hf_papers.py     # HuggingFace Daily Papers (중요도=추천수, 주력)
│     ├─ arxiv_client.py   # arXiv API (보충)
│     ├─ rss_client.py     # AI 뉴스 RSS
│     └─ github_client.py  # GitHub 트렌드
├─ site/                 # 생성되는 정적 사이트 (배포 대상)
├─ data/                 # 원자료/분석 결과 캐시 (gitignore)
├─ .github/workflows/daily.yml  # 매일 자동 실행 + Pages 배포
├─ requirements.txt
└─ .env.example
```

## 로컬 실행

```bash
pip install -r requirements.txt
cp .env.example .env        # ANTHROPIC_API_KEY 입력
py -3 -m src                # 오늘 날짜로 생성
```

브라우저에서 `site/index.html` 을 열면 결과 확인.

### 유용한 옵션

```bash
py -3 -m src --date 2026-07-08   # 특정 날짜로 생성
py -3 -m src --fetch-only        # 수집만 (Claude 호출 없이 data/ 저장 — 소스 점검용)
```

## 설정 (.env)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **필수** |
| `AIDL_MODEL` | `claude-opus-4-8` | 비용 절감 시 `claude-sonnet-5` / `claude-haiku-4-5` |
| `GITHUB_TOKEN` | — | GitHub 조회 rate limit 완화 (선택) |
| `AIDL_ARXIV_CATEGORIES` | `cs.AI,cs.LG,cs.CL,cs.CV` | arXiv 카테고리 |
| `AIDL_GITHUB_TOPICS` | `llm,agent,rag,machine-learning` | GitHub 토픽 |
| `AIDL_TIMEZONE` | `Asia/Seoul` | 날짜 기준 시간대 |

RSS 피드 목록은 `src/config.py` 의 `RSS_FEEDS` 에서 편집합니다.

## 자동 배포 (GitHub Pages)

1. 이 폴더를 GitHub 레포로 push
2. **Settings → Secrets → Actions** 에 `ANTHROPIC_API_KEY` 추가
3. **Settings → Pages → Source: GitHub Actions** 설정
4. 매일 KST 08:00 에 `daily.yml` 이 자동 실행 → 새 페이지 생성 → Pages 배포

`workflow_dispatch` 로 수동 실행도 가능합니다.

> Netlify 를 쓰려면 `site/` 를 publish 디렉터리로 지정하고,
> 빌드 커맨드를 `pip install -r requirements.txt && python -m src` 로 설정하면 됩니다.

## 동작 원리 메모

- 파이프라인은 스케줄러에서 **독립 실행**되어야 하므로 웹 소스는 RSS 로 구현 (안정적).
- Claude 는 `output_config.format` (structured outputs) 로 스키마를 강제해 항상 파싱 가능한 JSON 반환.
- `manifest.json` 이 전체 학습 기록의 인덱스이며 아카이브의 근거.
- `data/` 는 gitignore — 원자료/분석 결과는 로컬 캐시일 뿐 사이트 렌더링엔 불필요.
