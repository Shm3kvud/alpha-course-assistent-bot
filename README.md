# Alpha Course Assistant Bot

Telegram-бот-консультант с RAG по материалам платформы «Альфа Курсы»: подбирает курсы, статьи, шаблоны, вебинары, подкасты и калькуляторы под сферу, опыт и цель пользователя.

## Проблема

На платформе «Альфа Курсы» много разнородных материалов, и новичку сложно быстро понять, с чего начать. Начинающий предприниматель (например, 18-летний пользователь, который хочет открыть табачный магазин) теряется среди десятков курсов, сотен статей и шаблонов. Ему нужен помощник, который задаст уточняющие вопросы и порекомендует подходящее обучение.

## Решение

Telegram-бот-консультант с RAG-системой. Бот общается с пользователем, задаёт уточняющие вопросы, учитывает цель, опыт и сферу бизнеса, а затем рекомендует подходящие материалы на основе базы знаний платформы. Ответ конкретный и объяснимый: бот не просто даёт ссылку, а объясняет, почему материал подходит и что делать дальше.

## Целевая аудитория

- Новички — начинающие предприниматели, которые только хотят открыть бизнес.
- Мидл — предприниматели с опытом, которым нужно развитие или масштабирование.
- Сеньор — опытные предприниматели, которым нужны узкие и продвинутые темы.

## Гипотеза

Если помочь пользователю подобрать обучение через Telegram-бота за короткое время, ему будет комфортнее выбирать материалы, а платформа получит больше целевых переходов и продаж курсов. Бот даёт более точные рекомендации, чем обычный каталог, потому что учитывает потребности пользователя и работает с неполными данными.

## Функционал MVP

- Бот задаёт уточняющие вопросы о сфере, опыте и цели пользователя.
- Бот рекомендует материалы на основе запроса и базы знаний.
- Бот объясняет, почему рекомендует именно этот материал, и предлагает следующий шаг.
- Сохраняется история минимум одного чата.
- Бот периодически отправляет напоминания об обучении.
- Фишки: переключение между чатами / начало нового чата, аналитика запросов, серии рекомендаций.

## База знаний (актуальное состояние)

Источник — дамп платформы, восстановленный в Postgres (база `courses_for_bu`).
Векторная база — Postgres + pgvector (база `rag`, коллекция `knowledge`).

| Категория | Документов |
|---|---:|
| Курсы | 37 |
| Уроки | 512 |
| Доп. информация о курсах | 185 |
| Частые вопросы о курсах | 22 |
| Статьи | 855 |
| Шаблоны | 247 |
| Вебинары | 13 |
| Подкасты | 8 |
| Калькуляторы | 7 |
| Подписки | 1 |
| **Итого** | **1887** |

- Один материал = один `Document`: `page_content` (текст) + `metadata` (`id`, `url`, `source_type` и специфичные поля).
- `id` стабильный и уникальный (`course:…`, `article:…`, `lesson:{lesson_id}_{course_id}` и т.п.) — повторная индексация не плодит дубликаты.
- Векторная размерность — 384 (`intfloat/multilingual-e5-small`).

## Как работает RAG

Индексация (офлайн, CLI):

```
courses_for_bu
  -> db/db_loader.py        читает материалы, собирает Document (текст + metadata)
  -> rag/embeddings.py      текст -> вектор (e5, префикс passage:, нормализация)
  -> vector_db/vectorstore.py  запись в PGVector батчами (upsert по id)
```

Ответ на вопрос (онлайн):

```
вопрос
  -> rag/retriever.py       embedding запроса (query:) -> top-k по косинусу -> порог
  -> rag/pipeline.py        контекст + история диалога + системный промпт
  -> llm/client.py          GigaChat
  -> ответ пользователю
```

## Технический стек

- Python 3.12, пакетный менеджер **uv**
- **aiogram 3** — Telegram-бот (в работе)
- **sentence-transformers**, модель `intfloat/multilingual-e5-small` (fallback `e5-large`): префиксы `query:` / `passage:`, L2-нормализация, 384 измерения
- **Postgres 17 + pgvector** (`pgvector/pgvector:pg17`), базы `courses_for_bu`, `app`, `rag`
- **PGVector** (`langchain-postgres`) + **psycopg** — векторный поиск
- **GigaChat** (`langchain-gigachat`) — текстовая модель
- **pydantic-settings** — единые настройки из `.env`
- **Docker / Docker Compose**

## Структура проекта

```
alpha-course-assistent-bot/
├── config.py            # настройки из .env (Pydantic Settings)
├── docker-compose.yml   # Postgres + pgvector
├── Dockerfile           # пока пустой
├── pyproject.toml
├── uv.lock
├── .env.example
├── .python-version
├── README.md
│
├── bot/                 # Telegram-бот (aiogram) — в работе
│
├── db/
│   └── db_loader.py     # чтение исходной БД -> Document (текст + metadata)
│
├── vector_db/
│   └── vectorstore.py   # PGVector: создание коллекции, upsert, поиск
│
├── rag/
│   ├── embeddings.py    # обёртка e5 (префиксы, нормализация, fallback)
│   ├── retriever.py     # retrieve / aretrieve + фильтр по порогу
│   ├── ingest.py        # офлайн-индексация: fetch -> embed -> upsert
│   └── pipeline.py      # RAG-ответ: retrieve -> промпт -> LLM
│
├── llm/
│   ├── client.py        # GigaChat
│   └── prompts.py       # системный промпт
│
├── memory/
│   └── session.py       # история диалога (in-memory, последние 5 пар)
│
└── data/                # дамп и локальные данные (в git не попадает)
```

> `main.py` удалён (это была заглушка `uv`); точка входа бота ещё не готова.
> `.env`, `data/`, `.venv/`, `data_extracted.json` в `.gitignore`.

## Для разработчиков: как проверить без бота

Ниже — полный путь проверки RAG-части без Telegram. Команды для PowerShell (Windows).

### 0. Что нужно

- Python 3.12 и [uv](https://docs.astral.sh/uv/)
- Docker Desktop
- Файл дампа `data/alfa_course_hackathon.backup` (~19 МБ, в git не хранится)

### 1. Зависимости

```powershell
uv sync
```

### 2. Настроить `.env`

Скопируй `.env.example` в `.env` и заполни. Минимально для RAG:

```dotenv
SOURCE_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/courses_for_bu"
APP_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/app"
VECTOR_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/rag"
COLLECTION_NAME="knowledge"

EMBEDDING_MODEL="intfloat/multilingual-e5-small"
EMBEDDING_FALLBACK_MODEL="intfloat/multilingual-e5-large"
EMBEDDING_BATCH_SIZE="16"
EMBEDDING_DEVICE="cpu"

TOP_K="5"
SCORE_THRESHOLD="0.84"

GIGACHAT_API_KEY="..."   # нужен только для шага 7
```

### 3. Поднять Postgres

```powershell
docker compose up -d
docker compose ps        # ждём healthy
```

Если том с базой ещё пустой — создать нужные базы и восстановить дамп
(`courses_for_bu` создаётся автоматически из `POSTGRES_DB` в `docker-compose.yml`):

```powershell
docker compose exec -T db psql -U postgres -c "CREATE DATABASE rag;"
docker compose exec -T db psql -U postgres -d rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec -T db pg_restore -U postgres -d courses_for_bu --no-owner --no-privileges /data/alfa_course_hackathon.backup
```

Таблицы `langchain_pg_*` и расширение `vector` в `rag` создаёт сам `PGVector` при первом запуске.

### 4. Индексация

```powershell
$env:HF_HUB_OFFLINE="1"; $env:TRANSFORMERS_OFFLINE="1"
uv run python -m rag.ingest
```

Ожидаемо: счётчики по категориям, прогресс батчей (`200/1887`, …), итог. Первый запуск скачивает модель (~470 МБ для e5-small).

`HF_HUB_OFFLINE=1` обязателен, если сеть до HuggingFace нестабильна: модель уже в кэше, иначе `sentence-transformers` будет долго ретраить Hub.

### 5. Проверить, что записалось

```powershell
docker compose exec -T db psql -U postgres -d rag -c "SELECT count(*) FROM langchain_pg_embedding;"
```

Ожидаемо `1887` (при текущем дампе), без дублей.

### 6. Проверить поиск (без LLM)

```powershell
$env:HF_HUB_OFFLINE="1"; uv run python -c "import asyncio; from rag.retriever import aretrieve; docs=asyncio.run(aretrieve('хочу открыть табачный магазин', 3)); print('найдено:', len(docs)); [print(d.metadata.get('id'), '|', d.metadata.get('source_type'), '|', repr(d.page_content[:70])) for d in docs]"
```

Ожидаемо: 1–3 документа по теме и `source_type` вида `course` / `article`. Если `найдено: 0` — проверь порог `SCORE_THRESHOLD` (сейчас `0.84`).

### 7. Проверить полный RAG-ответ (нужен GigaChat API)

```powershell
uv run python -c "import asyncio; from rag.pipeline import answer; print(asyncio.run(answer('хочу открыть табачный магазин', 123)))"
```

Здесь `123` — любой `user_id` для истории (in-memory). Нужен `GIGACHAT_API_KEY` и сеть; без ключа шаг 6 достаточно, чтобы проверить retrieval.

### 8. Переиндексация

`ingest` каждый раз создаёт коллекцию заново (`pre_delete`), поэтому повторный запуск безопасен: дублей не будет, коллекция перезапишется.

### Частые проблемы

- **Порт 5432 занят** — поменяй в `docker-compose.yml` на `5433:5432` и поправь порт в URL в `.env`.
- **`ModuleNotFoundError`** — запускай из корня репозитория или через `uv run python -m ...`.
- **`connection refused`** — не поднят Docker/контейнер `courses-db`.
- **Долгий старт модели** — включи `HF_HUB_OFFLINE=1` (модель уже должна быть скачана).
- **Кракозябры в консоли** — кодировка Windows, не данные: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` и `$env:PYTHONIOENCODING="utf-8"`.
