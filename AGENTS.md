# AGENTS.md

AI 코딩 에이전트가 이 저장소에서 작업할 때 따르는 프로젝트 설명서다. 코드보다 이 문서와 `README.md`가 앞서면, 실제 파일(스키마, compose, requirements)을 우선한다.

---

## 1. 프로젝트 개요

- **프로젝트명**: AI 기반 주가 예측 및 뉴스 감성 분석 시스템
- **목적**: 개인 포트폴리오용 주가/ETF 시세, 뉴스 감성, 단기·중장기 전망을 한 대시보드에서 본다. Mac mini M2 로컬과 CPU 리눅스 서버에서 동작하는 것이 목표다.
- **핵심 사용자**: 운영자 본인 한 명. 공개 투자자문 서비스가 아니다. 화면에 예측을 보여줄 때는 참고용이며 투자 권유가 아니라는 점을 함께 드러낸다.
- **현재 단계**: 12절의 1~5단계 코드가 있다. 1~4단계는 로컬 Compose에서 실행을 확인했다. 영문 FinBERT, Prophet, DLinear는 코드만 있고 `requirements-ml.txt`를 설치하지 않아 실행하지 않았다.

README의 아키텍처 절과 로드맵 절은 비어 있다. 구현 범위는 아래 6절과 12절을 기준으로 하고, 새 단계를 시작하기 전에 사용자에게 확인한다.

확정된 업무 규칙: 종목 유니버스는 `backend/collectors/universe.py`의 국내 종목·ETF 7개, 일봉 소스는 yfinance(원시 가격), 뉴스는 Google News RSS, LightGBM 예측 기간은 5거래일, 경로 예측은 5~10거래일(기본 10), Ollama 모델은 `qwen3:8b`. 금리는 미국 국채 3M/5Y/10Y(yfinance `^IRX`/`^FVX`/`^TNX`)를 LightGBM 피처로만 쓰고, 한국 거래일 D에는 D보다 앞선 미국 날짜 값만 붙인다. 실적 일정은 yfinance를 ETF를 제외한 유니버스 종목에 쓰고, LightGBM에는 기준일 다음 거래일부터 5거래일 목표일까지의 발표 여부만 넣는다. EPS·서프라이즈 수치는 모델에 넣지 않는다.

## 2. 기술 스택

| 구분 | 내용 |
|---|---|
| 백엔드 | Python 3.11, FastAPI, Uvicorn. 진입점은 `backend/main.py`의 `app` (`uvicorn main:app`) |
| 프론트 | Node.js 24, Next.js 16 (App Router, Turbopack), React 19, Tailwind CSS 4. 개발 서버 `npm run dev`, 포트 3000 |
| DB | TimescaleDB (PostgreSQL 15) + SQLAlchemy 2.0 asyncio + asyncpg |
| 캐시 | Redis 7. 클라이언트만 의존성에 있고, 사용 코드와 큐 라이브러리는 없다 |
| 데이터/모델 | API 이미지: pandas, LightGBM, yfinance. 호스트 venv 전용 `backend/requirements-ml.txt`: torch, transformers(FinBERT), prophet. Ollama는 호스트에서 실행 |
| 수집 | `httpx` + BeautifulSoup4, yfinance. Playwright는 동적 페이지가 필요할 때만 |
| 테스트 | 자동 테스트 없음. 프론트는 `npx tsc --noEmit`, `npx eslint .` |
| 실행 | Docker Compose. 타임존 `Asia/Seoul` |
| 패키지 | 백엔드 `pip` / `backend/requirements.txt`, 프론트 `npm` / `frontend/package-lock.json` |

버전 제약: 백엔드는 Python 3.11 문법. Pydantic v2, SQLAlchemy 2.x 스타일만 사용한다. Next.js 16은 이전 버전과 API가 다르다(`params`가 Promise 등). 프론트 코드를 쓰기 전에 `frontend/AGENTS.md`의 안내대로 `node_modules/next/dist/docs/`를 확인한다.

## 3. 폴더 구조

```
.
├── backend/                         # FastAPI. 호스트 소스가 컨테이너 /app 에 마운트됨
│   ├── Dockerfile                   # python:3.11-slim, uvicorn --reload
│   ├── requirements.txt             # API 컨테이너 의존성
│   ├── requirements-ml.txt          # 호스트 venv(MPS) 배치 전용
│   ├── main.py                      # 앱 생성, CORS, 예외 핸들러, 라우터 등록
│   ├── core/                        # 설정(환경변수), 로깅
│   ├── db/session.py                # async 엔진, 세션
│   ├── models/                      # ORM (init.sql 과 1:1)
│   ├── schemas/                     # Pydantic 응답 스키마, ApiResponse
│   ├── repositories/                # 조회 쿼리
│   ├── routers/                     # health, stocks, news, predictions
│   ├── collectors/                  # universe.py, prices/, news/, rates/, earnings/ (CLI: python -m ...run)
│   ├── sentiment/                   # finbert.py, ollama_client.py, service.py
│   ├── prediction/                  # 피처, LightGBM, Prophet, DLinear, 결과 기록
│   ├── scripts/seed_stocks.py       # 유니버스를 stocks 에 등록
│   └── artifacts/                   # 학습 산출물 (gitignore)
├── frontend/                        # Next.js. node_modules, .next 는 컨테이너 전용 볼륨
│   ├── Dockerfile                   # node:24-alpine, npm ci && npm run dev
│   ├── app/                         # 페이지 (/, /stocks/[symbol])
│   ├── components/                  # 화면 컴포넌트 (클라이언트 페칭)
│   ├── hooks/useApi.ts
│   └── lib/                         # api 래퍼, 타입, 포맷, 모델 표시 정보
├── docker/timescaledb/init.sql      # 최초 기동 시에만 실행되는 스키마
├── docker-compose.yml
├── README.md                        # 제품 방향. 아키텍처/로드맵 본문은 비어 있음
└── AGENTS.md
```

`init.sql`은 데이터 디렉터리가 비어 있는 첫 기동에서만 적용된다. 볼륨이 이미 있으면 파일을 고쳐도 DB에 반영되지 않는다. 스키마를 바꿀 때는 사용자에게 알리고, 기존 볼륨을 지울지 마이그레이션 SQL을 별도로 둘지 확인한 뒤 진행한다.

### 작업 시 빠른 안내

| 목적 | 경로 |
|---|---|
| 서비스 구성, 포트, 환경변수 | `docker-compose.yml` |
| 테이블, 하이퍼테이블, 인덱스 | `docker/timescaledb/init.sql` |
| API 진입점 | `backend/main.py` |
| DB 세션, 모델 | `backend/db/`, `backend/models/` |
| 종목 유니버스 | `backend/collectors/universe.py` |
| 시세 수집 | `backend/collectors/prices/` |
| 국채 금리 수집 | `backend/collectors/rates/` |
| 실적 일정 수집 | `backend/collectors/earnings/` |
| 기존 볼륨 마이그레이션 | `docker/timescaledb/migrations/` |
| 뉴스 수집·감성 | `backend/collectors/news/`, `backend/sentiment/` |
| 예측 | `backend/prediction/` |
| 화면 | `frontend/app/`, `frontend/components/` |
| 백엔드 의존성 | `backend/requirements.txt` |
| 제품 방향 | `README.md` |

의도한 데이터 흐름:

```
시세/뉴스 수집 → TimescaleDB
감성·예측 배치 → news_sentiments, ai_predictions
Next.js(:3000) → FastAPI(:8000) → TimescaleDB(:5432), Redis(:6379)
```

브라우저는 `NEXT_PUBLIC_API_URL`(현재 `http://localhost:8000`)로 API를 직접 호출한다. FastAPI에 이 Origin에 대한 CORS가 필요하다.

## 4. 코딩 컨벤션

### 4.1 공통

- API JSON은 `{ "success": true, "data": ..., "error": null }` 형태로 맞춘다. 실패 시 `success: false`, `data: null`, `error`에 사용자용 짧은 메시지.
- 식별자(변수, 함수, 파일, 테이블)는 영어. 주석과 사용자에게 보이는 문장은 한국어.
- 커밋되지 않은 디버그 출력(`print`, `console.log`)은 확인 후 제거한다.
- 패키지를 추가하기 전에 `requirements.txt`와 README 계획에 같은 역할이 있는지 본다. README에만 있고 의존성에 없는 라이브러리(PyTorch, Prophet, Playwright, Ollama)는 해당 기능을 구현하는 작업에서만 추가하고, 추가 사실을 사용자에게 알린다.
- 실행 환경은 Mac mini M2(MPS)와 CPU 서버다. CUDA 전용 경로를 기본으로 두지 않는다.

### 4.2 `backend/`

- 스타일: PEP 8, 함수·변수 `snake_case`, 클래스 `PascalCase`, 상수 `UPPER_SNAKE_CASE`.
- 타입 힌트를 붙인다. 요청·응답 스키마는 Pydantic v2 `BaseModel`.
- DB 접근은 SQLAlchemy 2.0 asyncio. 사용자 입력을 SQL 문자열에 이어 붙이지 않는다.
- 가격·점수·확률은 `float`로 느슨하게 다루기보다 `Numeric` / `Decimal`과 스키마 스케일에 맞춘다.
- 시계열 테이블은 `time`이 기본키에 포함되어야 하이퍼테이블이 된다. 새 시계열 테이블도 이 패턴을 따른다.
- 라우터는 도메인별로 나누고 `main.py`는 앱 생성, CORS, 라우터 등록, 수명주기만 담당한다.

### 4.3 `frontend/`

- 기존 앱 코드가 없다. 처음 만들 때 App Router + TypeScript로 둔다.
- 컴포넌트 `PascalCase`, 함수·훅 `camelCase`, 파일명은 같은 폴더의 기존 파일을 따른다.
- 데이터 페칭과 표시를 분리한다. 컴포넌트 안에 API 베이스 URL을 하드코딩하지 않고 `NEXT_PUBLIC_API_URL`을 쓴다.
- 사용자 입력과 뉴스 제목·요약을 그대로 HTML로 주입하지 않는다.

## 5. 보안 필수 규칙

- SQL은 바인딩 파라미터 또는 ORM만 사용한다.
- 뉴스 제목, 요약, 종목명은 화면에 넣을 때 이스케이프한다.
- 상태를 바꾸는 요청에는 단일 사용자 로컬 앱이라도 무분별한 공개 쓰기를 열지 않는다. 인증을 넣기 전에는 수집·학습 트리거를 인터넷에 열어 두지 않는다.
- DB 비밀번호, API 키, 모델 토큰을 소스에 하드코딩하지 않는다. 기본값도 두지 않는다. DB 비밀번호는 루트 `.env`의 `POSTGRES_PASSWORD`에만 있고, 없으면 compose와 백엔드 설정이 기동을 거부한다. `.env`는 커밋하지 않는다.
- compose의 모든 포트는 `127.0.0.1`에만 바인딩한다. 외부 접속이 필요해지면 인증을 먼저 넣고 사용자에게 확인한다.
- 외부 시세·뉴스 사이트를 스크랩할 때 인증 쿠키나 계정 정보를 저장소에 넣지 않는다.

## 6. 아키텍처 원칙

관심사별로 나눈다.

| 계층 | 책임 |
|---|---|
| `frontend` | 조회와 입력. DB·모델 호출 금지 |
| 라우터 | 요청 검증, 상태 코드, 응답 형태 |
| 서비스 | 수집, 감성, 예측 흐름 |
| DB 계층 | 쿼리와 세션만 |

한 함수는 한 가지 일만 한다. 대략 50줄을 넘겨 역할이 섞이면, 나누기 전에 계획을 짧게 알린다. 비슷한 코드가 보여도 바로 공통화하지 않고, 두 번째 사용처가 생기기 전에는 둔다.

### 데이터 모델

`init.sql`이 기준 스키마다.

| 테이블 | 역할 |
|---|---|
| `stocks` | `symbol` PK, `name`, `market`, `sector`, `is_active` |
| `stock_daily_candles` | 일봉 하이퍼테이블. 청크 1개월. 가격·거래량·등락률 |
| `stock_minute_candles` | 분봉 하이퍼테이블. 청크 7일 |
| `news_sentiments` | 뉴스 하이퍼테이블. `sentiment_label`, `sentiment_score`, `impact_score`. `(time, url)` 유니크(하이퍼테이블 유니크 제약은 `time`을 포함해야 함) |
| `ai_predictions` | 예측 하이퍼테이블. 모델명, 목표일, 예측 종가, 상·하한, `direction_signal`, `win_probability` |
| `macro_daily_rates` | 거시 금리 하이퍼테이블. 청크 1년. `(time, series_code)` PK, `value NUMERIC(8,4)`(%), `source`. `time`은 시리즈 현지 날짜 00:00 |
| `earnings_events` | 실적 일정 하이퍼테이블. 청크 1년. `(time, symbol)` PK. `time`은 한국 날짜 00:00. EPS 예상·발표·서프라이즈는 없을 수 있다 |

종목을 저장하지 않은 채 캔들이나 예측을 넣지 않는다. `news_sentiments.symbol`만 NULL을 허용한다(종목 무관 매크로 뉴스).

### 모델 역할 (README 계획)

구현 순서를 건너뛰지 않는다. 짧은 구간 방향은 LightGBM(의존성에 있음). 계절·추세 구간은 Prophet. 과거 60일 패턴으로 5~10일 경로는 PatchTST / DLinear. 영문 감성은 FinBERT, 국내 뉴스는 로컬 Ollama. 뒤의 네 가지는 해당 단계에 들어가기 전에 의존성 추가를 알린다.

예측 API는 확률과 구간을 함께 돌려준다. 확정 가격처럼 단정하는 문장을 응답이나 UI 카피에 쓰지 않는다.

## 7. 에러 처리 & 로깅

- 응답 `error`에는 스택 트레이스, SQL, 접속 정보를 넣지 않는다.
- 백엔드는 표준 라이브러리 `logging`을 쓴다. Sentry 등 새 수집 체계는 도입 전에 묻는다.
- 수집 실패는 종목·소스·시각을 로그에 남기고, 이미 쌓인 캔들·뉴스를 지우지 않는다.
- 외부 HTTP는 타임아웃을 둔다. 재시도는 횟수 상한을 명시한다.

## 8. 테스트 정책

자동 테스트가 없다. 동작을 바꾼 뒤에는 아래를 확인했다고 보고한다.

- `docker compose up` 후 TimescaleDB·Redis 헬스체크가 통과하는지
- `GET /health` (백엔드를 만든 뒤)가 200인지
- 수정한 API를 프론트 화면 또는 `curl`로 호출했는지
- 스키마를 바꿨다면 빈 볼륨 기준인지, 기존 볼륨 마이그레이션인지

스키마 변경, 파일 삭제, 폴더 구조 변경은 영향 파일 목록을 먼저 알린다.

## 9. 코드 스타일 예시

```python
# ❌ Bad — SQL 이어 붙이기, float 가격, 디버그 출력
@app.get("/candles/{symbol}")
async def candles(symbol: str):
    rows = await session.execute(text(f"SELECT * FROM stock_daily_candles WHERE symbol = '{symbol}'"))
    print(rows)
    return rows

# ✅ Good — 바인딩, 소수 유지, 공통 응답
@router.get("/candles/{symbol}")
async def candles(symbol: str, session: AsyncSession = Depends(get_session)):
    stmt = (
        select(StockDailyCandle)
        .where(StockDailyCandle.symbol == symbol)
        .order_by(StockDailyCandle.time.desc())
        .limit(120)
    )
    rows = (await session.scalars(stmt)).all()
    return {"success": True, "data": [CandleOut.model_validate(r) for r in rows], "error": None}
```

```tsx
// ❌ Bad — API 주소 하드코딩, HTML 주입
<div dangerouslySetInnerHTML={{ __html: article.title }} />

// ✅ Good — 환경변수, 텍스트 노드
const api = process.env.NEXT_PUBLIC_API_URL;
<p>{article.title}</p>
```

## 10. AI 에이전트가 반드시 지킬 규칙

- 지금 저장소에 없는 모듈을 있는 것처럼 가정하지 않는다. 파일 목록과 `init.sql`, `requirements.txt`를 확인한다.
- 수집기·감성·딥러닝을 한 번에 넣지 않는다. 아래 12절 순서에서 사용자가 지정한 단계만 구현한다.
- 파일을 삭제하거나 스키마·폴더를 크게 바꾸기 전에 계획과 영향 범위를 알린다.
- 종목 유니버스, 거래소 코드, 예측 기간처럼 README에 없는 업무 규칙은 정하지 말고 묻는다.
- `git push`와 히스토리를 되돌리는 명령은 사용자가 승인하기 전에는 실행하지 않는다.
- 커밋은 사용자가 명시적으로 요청한 뒤에만 한다.
- `.env`, `node_modules`, `.next`, `__pycache__`, 모델 가중치, DB 볼륨은 커밋하지 않는다. 앱 코드를 처음 넣을 때 `.gitignore`가 없으면 그때 추가한다.

## 11. Git 커밋 규칙

사용자가 커밋을 요청하면 논리적 단위마다 하나의 커밋으로 나눈다. 목적이 다른 변경은 묶지 않는다. 제목은 50자 안팎으로 하고, 앞에 `(Cursor ai)`를 붙인다.

```
(Cursor ai) <type>(<scope>): <제목>

<본문 - 무엇을, 왜 바꿨는지>
```

type: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `chore`, `perf`.

예시:

```
(Cursor ai) feat(api): 일봉 조회 API 추가

- stock_daily_candles 를 symbol 기준으로 최신순 반환
- 공통 success/data/error 응답 사용
```

## 12. 프로젝트별 추가 규칙

로컬 포트: Postgres `5432`, Redis `6379`, API `8000`, 웹 `3000`. 타임존은 `Asia/Seoul`.

로컬 실행 순서:

```bash
cp .env.example .env                                              # 최초 1회, POSTGRES_PASSWORD 변경
docker compose up -d                                              # 4개 서비스
docker compose exec backend python -m scripts.seed_stocks         # 종목 등록
docker compose exec backend python -m collectors.prices.run       # 일봉 (이력 없으면 3년, 이후 증분)
docker compose exec backend python -m collectors.news.run --lang ko   # 국내 뉴스 + Ollama 감성
docker compose exec backend python -m collectors.rates.run        # 미국 국채 금리 (기존 볼륨은 migrations/001 먼저 적용)
docker compose exec backend python -m collectors.earnings.run     # 실적 일정 (ETF 제외, 기존 볼륨은 migrations/002 먼저 적용)
docker compose exec backend python -m prediction.run_lightgbm     # 5거래일 방향 예측 (금리·실적 일정 포함, --no-earnings --evaluate-only 로 비교)
# 호스트 venv (requirements-ml.txt 설치 후, backend 디렉터리에서 set -a; source ../.env; set +a)
python -m collectors.news.run --lang en                           # 영문 뉴스 + FinBERT(MPS)
python -m prediction.run_forecast --model prophet                 # 추세 + 80% 구간
python -m prediction.run_forecast --model dlinear                 # 60일 입력 경로 + 80% 구간
```

macOS Docker 컨테이너에서는 MPS를 쓸 수 없다. GPU가 필요한 배치는 호스트 venv에서 돌린다. 컨테이너에서 호스트 Ollama는 `host.docker.internal:11434`로 호출한다. 수집·학습은 CLI로만 실행하고 API로 트리거를 열지 않는다.

`win_probability`는 모든 모델에서 "목표일 종가가 기준일 종가보다 높을 확률"이다. LightGBM은 0.55 이상 `up`, 0.45 이하 `down`, 그 사이 `flat`. 목표일 계산은 평일 기준이고 한국 공휴일은 반영하지 않는다.

권장 구현 순서 (사용자가 단계를 지정하면 그 단계만):

1. FastAPI 골격, DB 세션, `/health`, 종목·일봉 조회. Next.js에서 그 조회를 표시.
2. 일봉 수집을 `stock_daily_candles`에 적재.
3. 뉴스 수집과 감성 점수를 `news_sentiments`에 적재. 영문은 FinBERT, 국내는 Ollama.
4. LightGBM으로 `ai_predictions`에 N일 방향·확률 기록.
5. Prophet 추세, 이어서 PatchTST/DLinear 경로. 대시보드에 구간과 함께 표시.

Redis는 연결 설정만 준비되어 있다. 캐시로 쓸지 작업 큐로 쓸지는 그 기능이 필요해질 때 사용자에게 확인한다.

예측 결과는 `model_name`, `target_date`, `direction_signal`, `win_probability`, 가능하면 `predicted_close`와 상·하한을 채운다. 라벨 값은 스키마의 `VARCHAR(10)`에 들어가는 짧은 토큰(`up`, `down`, `flat`, `positive`, `negative`, `neutral`)으로 맞춘다.
