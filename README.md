# 📈 AI 기반 주가 예측 및 뉴스 감성 분석 시스템

> **프로젝트 개요:** Mac mini M2 로컬 환경 및 CPU 리눅스 서버 배포를 목표로 하는 개인 포트폴리오용 주가/ETF 예측 및 전망 대시보드 시스템.

---

## 1. 시스템 아키텍처 (System Architecture)


---

## 2. 모듈별 핵심 전략

### 2.1. 뉴스 스크래핑 & NLP 감성 분석 (Sentiment Pipeline)
* **수집 대상:** Bloomberg, Reuters (해외 Macro), Naver Finance / 연합인포맥스 (국내 특화)
* **수집 도구:** `Playwright` (Headless 브라우저) 또는 `httpx` + `BeautifulSoup4`
* **M2 MPS 파이프라인 (비용 $0 로컬 AI):**
  * **영문 뉴스:** `ProsusAI/finbert` (HuggingFace) 모델을 PyTorch `mps` 디바이스로 연동해 **Positive / Negative / Neutral** 감성 점수 산출.
  * **국내 뉴스:** `Ollama` (Llama-3 8B / Qwen2.5) 로컬 구동을 통한 뉴스 영향도 평가.
* **Feature 생성:** 당일 및 N일간의 **평균 감성 점수(Sentiment Score)** 및 **뉴스 언급량(Volume)**을 시계열 지표로 수치화.

### 2.2. 주가 예측 및 전망 모델 (Prediction Engine)
별도의 고가 GPU 서버 없이 **Mac mini M2 (MPS)** 및 **CPU 서버**에서 고속 추론 가능한 모델 조합:

| 구분 | AI/ML 모델 | 특징 및 용도 |
| :--- | :--- | :--- |
| **단기 모멘텀** | **LightGBM / CatBoost** | 기술적 지표, 뉴스 감성, 국채 금리, 실적 일정 여부를 입력받아 N일 뒤 상방/하방 확률 예측 |
| **중장기 추세** | **Prophet / NeuralProphet** | 계절성, 이벤트 효과를 반영한 미래 가격 추세선 및 신뢰구간(Upper/Lower) 형성 |
| **시계열 딥러닝** | **PatchTST / DLinear** | M2 MPS 환경에서 과거 60일 패턴 기반 향후 5~10일 가격 경로 추정 |

### 2.3. 국채 금리 피처 (Macro Rates)
금리 방향과 장단기 금리차를 LightGBM 단기 방향 예측의 입력으로 쓴다. Prophet, DLinear 에는 넣지 않았다.

* **데이터 소스:** yfinance (API 키 불필요). 일별 종가 기준, 단위는 % (예: `4.05` = 4.05%)

| 코드 | 내용 | yfinance 티커 |
| :--- | :--- | :--- |
| `US3M` | 미국 국채 3개월 | `^IRX` |
| `US5Y` | 미국 국채 5년 | `^FVX` |
| `US10Y` | 미국 국채 10년 | `^TNX` |

* **저장:** `macro_daily_rates` 하이퍼테이블 (`time`, `series_code`, `value NUMERIC(8,4)`, `source`). 기본키 `(time, series_code)`, `time` 은 뉴욕 현지 날짜 00:00.
* **수집:** 이력이 없으면 약 3년치, 이후에는 마지막 날짜 7일 전부터 다시 받아 덮어쓴다(멱등).
* **LightGBM 피처** (`backend/prediction/features.py` 의 `RATE_FEATURES`)

| 피처 | 의미 |
| :--- | :--- |
| `us10y_chg_5` | 10년물 금리 5영업일 변화(%p) |
| `us10y_chg_20` | 10년물 금리 20영업일 변화(%p) |
| `us3m_chg_20` | 3개월물 금리 20영업일 변화(%p) |
| `us_spread_10y_3m` | 장단기 금리차 (10년 − 3개월, %p) |

* **미래 정보 차단:** 미국 장 마감(뉴욕 16:00)은 한국 시간으로 다음 날 아침이다. 한국 거래일 D 의 피처에는 **D 보다 앞선 미국 날짜**의 금리만 붙인다(`merge_asof`, 같은 날짜 제외). 예: 한국 2026-10-12(월) 행은 미국 2026-10-09(금) 금리를 쓴다. 미국 휴장일은 직전 값을 이어 쓴다.
* **실행**
  ```bash
  # 기존 DB 볼륨에 테이블 추가 (새 볼륨은 init.sql 에 포함되어 있어 불필요)
  docker compose exec -T timescaledb sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < docker/timescaledb/migrations/001_macro_daily_rates.sql

  docker compose exec backend python -m collectors.rates.run                 # 3개 시리즈 수집
  docker compose exec backend python -m prediction.run_lightgbm              # 금리 포함 (기본)
  docker compose exec backend python -m prediction.run_lightgbm --no-rates --evaluate-only  # 금리 제외 비교, 기록 안 함
  ```
  금리가 비어 있으면 `run_lightgbm` 은 수집을 먼저 하라는 메시지와 함께 멈춘다.
* **검증 결과 (2026-10-12, 7종목, 5거래일 방향, walk-forward 4구간 × 60거래일)**

| 피처 | 평균 정확도 | 평균 log loss | 다수 클래스 기준선 |
| :--- | :--- | :--- | :--- |
| 가격만 | 0.512 | 0.756 | 0.518 |
| 가격 + 금리 | 0.507 | 0.762 | 0.518 |

  이 기간·종목에서는 금리 피처가 정확도를 올리지 못했고 두 경우 모두 기준선 수준이다. 구간별로는 첫 구간(2025-10~2026-01)에서 0.507 → 0.567 로 올랐지만 다른 구간에서는 내려갔다. 예측은 참고용이며 투자 권유가 아니다.

### 2.4. 실적 발표 일정 (Earnings Calendar)
다가오는 실적 발표를 종목 화면에서 미리 보여주고, LightGBM 에는 예측 구간에 발표가 들어 있는지만 넣는다. Prophet, DLinear 에는 넣지 않았다. ETF(KODEX 200, KODEX 코스닥150)는 개별 실적이 없어 수집하지 않는다.

* **데이터 소스:** yfinance `get_earnings_dates` (API 키 불필요). 종목당 최근 약 6년과 예정일을 받는다.
* **저장:** `earnings_events` 하이퍼테이블. 기본키 `(time, symbol)`, `time` 은 발표 시각을 한국 날짜 00:00 으로 맞춘 값. `eps_estimate`, `eps_reported`, `surprise_pct`(Yahoo 가 주는 예상 대비 %, 예: `39.96` = 39.96%)는 비어 있을 수 있다.
* **수집:** 같은 날짜가 여러 번이면 발표 EPS 가 있는 행을 남긴다. 다시 실행하면 덮어쓰고, 응답에 없는 **오늘 이후** 일정만 지운다. 과거 행은 유지한다. 응답이 비어 있으면 기존 일정을 지우지 않는다.
* **화면:** 목록에는 다음 발표일을 붙이고, 14일 이내면 강조한다. 종목 화면에는 다음 발표·시장 예상 EPS·최근 발표 수치를 보여 준다. 최근 일봉 기준 5거래일 안에 발표가 있으면 그 사실을 함께 적는다.
* **LightGBM 피처** (`EARNINGS_FEATURES`): `earnings_in_horizon`. 한국 거래일 D 의 피처는 **D 다음 거래일부터 5거래일 목표일까지** 발표가 있으면 1, 없으면 0. 거래일은 주말과 `backend/prediction/holidays.py` 의 한국거래소 휴장일을 건너뛴다. 당일 발표는 빼 둔다. 장중·장후에 나왔을 수 있어 그날 종가에 이미 반영됐을 수 있다.
* **모델에 넣지 않는 것:** EPS 예상·발표·서프라이즈. 이 수치는 발표 뒤에야 확정되고, yfinance 는 과거 시점의 예상치를 주지 않는다. 화면 참고용이다.
* **한계:** yfinance 는 일정이 언제 공지됐는지 주지 않는다. 과거 학습은 실제 발표일을 그 전부터 알려진 일정으로 본다. 직전에 바뀐 일정은 반영하지 못한다. 국내 종목은 누락·지연이 있을 수 있다.
* **실행**
  ```bash
  # 기존 DB 볼륨에 테이블 추가 (새 볼륨은 init.sql 에 포함되어 있어 불필요)
  docker compose exec -T timescaledb sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < docker/timescaledb/migrations/002_earnings_events.sql

  docker compose exec backend python -m collectors.earnings.run
  docker compose exec backend python -m prediction.run_lightgbm
  docker compose exec backend python -m prediction.run_lightgbm --no-earnings --evaluate-only
  ```
  실적 일정이 비어 있으면 `run_lightgbm` 은 수집을 먼저 하라는 메시지와 함께 멈춘다.
* **검증 결과 (2026-10-29, 7종목, 일봉은 2026-10-29까지, 5거래일 방향, 금리 포함, walk-forward 4구간 × 60거래일)**

| 피처 | 평균 정확도 | 평균 log loss | 다수 클래스 기준선 |
| :--- | :--- | :--- | :--- |
| 가격 + 금리 | 0.479 | 0.819 | 0.483 |
| 가격 + 금리 + 실적 일정 | 0.479 | 0.804 | 0.483 |

  정확도는 같고 log loss 만 0.819 에서 0.804 로 낮아졌다. 구간별 정확도는 2026-04~07 에서 0.381 → 0.419 로 올랐고, 2025-10~2026-01 에서는 0.617 → 0.590 으로 내려갔다. 두 경우 모두 기준선 수준이다. 예측은 참고용이며 투자 권유가 아니다. 휴장일을 반영한 뒤의 비교는 2.5절에 있다.

### 2.5. 운영, 휴장일, 검증 성적
모델을 더 얹기보다, 이미 있는 화면이 최신 시세와 실제 거래일을 기준으로 동작하게 둔다.

* **휴장일:** 목표일과 실적 구간은 평일만이 아니라 한국거래소 휴장일을 건너뛴다. 목록은 2023-01-01부터 2027-10-29까지다. 수능일은 개장 시각만 늦는 날이라 휴장에 넣지 않았다. 2026-06-03(지방선거)과 2026-07-17(제헌절)은 거래소 휴장 공시를 반영했다. 목록 끝 이후의 임시 휴장은 평일로 세므로, 2027년 11월 전에 `backend/prediction/holidays.py` 를 늘린다. 화면의 5거래일 판정도 `GET /calendar/holidays` 의 같은 목록을 쓴다.
* **검증 성적:** LightGBM 카드의 상승 확률 아래에 최근 walk-forward 평균 정확도와 기준선을 적는다. 기준선은 그 검증 구간에서 많이 나온 방향(상승 또는 하락)을 항상 고른 정확도다. 산출물 `backend/artifacts/lightgbm_dir_5d.json` 이 없으면 이 문장은 나오지 않는다.
* **장 마감 수집:** `scripts/daily_close.sh` 가 일봉, 금리, 실적 일정, 국내 뉴스, LightGBM 순서로 돈다. 일봉이 실패하면 예측은 건너뛴다. 뉴스나 금리, 실적이 실패해도 시세가 있으면 감성 없이 학습한다. 수집 트리거 API 는 열지 않는다. macOS launchd 는 월~금 18:00(맥 로컬 시각, 이 장비는 Asia/Seoul)에 스크립트를 호출한다.
  ```bash
  chmod +x scripts/daily_close.sh
  cp scripts/com.geon.stock-insight.daily.plist ~/Library/LaunchAgents/
  launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.geon.stock-insight.daily.plist 2>/dev/null || true
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.geon.stock-insight.daily.plist
  ```
  저장소 경로를 옮기면 plist 의 경로를 고친 뒤 다시 bootstrap 한다. Docker 가 떠 있어야 하고, 국내 뉴스는 호스트 Ollama 가 떠 있어야 한다. 로그는 `logs/daily_close.log` 다.
* **뉴스 감성:** 매일 수집은 하되, LightGBM 기본 학습에는 넣지 않는다. `--with-sentiment` 는 감성 시작일이 일봉 시작보다 60일을 넘겨 늦으면 멈추고, 이력이 학습 구간을 덮은 뒤에만 쓰라고 알린다. 그 전에는 감성 피처 대부분이 0이라 최근 구간만 표시하는 변수가 된다.
* **휴장일 반영 후 검증 (2026-10-29, 같은 walk-forward 설정)**

| 피처 | 평균 정확도 | 평균 log loss | 다수 클래스 기준선 |
| :--- | :--- | :--- | :--- |
| 가격 + 금리 | 0.479 | 0.819 | 0.483 |
| 가격 + 금리 + 실적 일정 | 0.478 | 0.809 | 0.483 |

  휴장일을 넣은 뒤에도 정확도는 기준선과 같다. 실적 일정은 log loss 를 0.819 에서 0.809 로만 낮춘다. 화면의 검증 문장도 이 학습 산출물을 읽는다.

---

## 3. 단계별 개발 로드맵 (Roadmap)

