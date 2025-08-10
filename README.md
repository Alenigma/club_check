## Club Check

### Требования
- Python 3.13
- PostgreSQL 14+
- Docker + Docker Compose

### Конфигурация (.env)
Создайте `.env`:

CLUB_CHECK_APP_NAME="Club Check API"
CLUB_CHECK_ENVIRONMENT=development
# сгенерируйте: openssl rand -hex 32
CLUB_CHECK_SECRET_KEY=<HEX>
CLUB_CHECK_JWT_ALGORITHM=HS256
CLUB_CHECK_ACCESS_TOKEN_EXPIRE_MINUTES=60
# PostgreSQL (dev)
CLUB_CHECK_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/club_check
# CORS, через запятую
CLUB_CHECK_CORS_ORIGINS=http://localhost:8000,http://localhost:5173
# Флаги старта
CLUB_CHECK_CREATE_TABLES_ON_STARTUP=false
CLUB_CHECK_SEED_ON_STARTUP=false
# BLE
CLUB_CHECK_ENABLE_BLE_CHECK=false

### Установка зависимостей
pip install -r requirements.txt

### Миграции (Alembic)
- Создайте БД (например, `club_check`).
- Прогон миграций:
export CLUB_CHECK_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/club_check
alembic upgrade head

Создание новой миграции:
alembic revision --autogenerate -m "<message>"
alembic upgrade head

### Запуск в development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
- В dev можно временно включить `CLUB_CHECK_CREATE_TABLES_ON_STARTUP=true` если нет миграций.
- На проде сиды выключены: `CLUB_CHECK_SEED_ON_STARTUP=false`.

### Запуск в production (за обратным прокси)
uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port 8000
- Прогнать миграции перед запуском.

### Docker / Compose
Сборка и запуск:
docker compose up --build

### Тесты
# Игнорировать .env, чтобы тесты были изолированы
export CLUB_CHECK_USE_ENV_FILE=false
python -m pytest -q