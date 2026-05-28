#!/usr/bin/env bash
set -euo pipefail # 确保脚本在遇到错误时立即退出

HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
INIT_DATABASE_ENABLED=${INIT_DATABASE_ENABLED:-"false"}
MIGRATION_ENABLED=${MIGRATION_ENABLED:-"false"}
INIT_ADMIN_ENABLED=${INIT_ADMIN_ENABLED:-"false"}

if [[ "${INIT_DATABASE_ENABLED}" == "true" ]]; then
  echo "Ensuring database exists"
  (cd "$(dirname "$0")/.." && python -m scripts.ensure_database)
fi

if [[ "${MIGRATION_ENABLED}" == "true" ]]; then
  echo "Running migrations"
  pushd "$(dirname "$0")/../migrations" > /dev/null
  alembic upgrade head
  popd > /dev/null
fi

if [[ "${INIT_ADMIN_ENABLED}" == "true" ]]; then
  echo "Initializing default admin user"
  (cd "$(dirname "$0")/.." && python -m scripts.seed_users)
fi

echo "fastapi run on $HOST:$PORT with $WORKERS workers"
exec uvicorn app:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
