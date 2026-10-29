#!/bin/zsh
# 한국 장 마감 이후 로컬 수집. API 로 수집을 열지 않는다.
# 뉴스가 실패해도 시세가 모이면 LightGBM 은 감성 없이 학습한다.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
mkdir -p logs

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  if ! docker compose exec -T backend python -m collectors.prices.run; then
    echo "일봉 수집 실패. 예측은 건너뜁니다."
    exit 1
  fi
  docker compose exec -T backend python -m collectors.rates.run || echo "금리 수집 실패"
  docker compose exec -T backend python -m collectors.earnings.run || echo "실적 일정 수집 실패"
  docker compose exec -T backend python -m collectors.news.run --lang ko || echo "국내 뉴스 수집 실패. 감성 피처는 켜지 않습니다."
  docker compose exec -T backend python -m prediction.run_lightgbm
} >> logs/daily_close.log 2>&1
