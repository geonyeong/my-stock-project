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

---

## 3. 단계별 개발 로드맵 (Roadmap)

