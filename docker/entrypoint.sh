#!/usr/bin/env sh
set -e

export CLUB_CHECK_DATABASE_URL=${CLUB_CHECK_DATABASE_URL:-"sqlite:///./club_check.db"}

alembic upgrade head

exec uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port 8000