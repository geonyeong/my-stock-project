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
| **단기 모멘텀** | **LightGBM / CatBoost** | 기술적 지표 + 뉴스 감성 점수를 입력받아 N일 뒤 상방/하방 확률 예측 |
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

---

## 3. 단계별 개발 로드맵 (Roadmap)

