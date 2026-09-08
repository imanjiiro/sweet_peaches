# Calc Service — стартовый репозиторий курса «Архитектура и проектирование веб-приложений»

Учебный веб-сервис с вычислительным ядром. Заготовка для командного проекта: замените пример (численное интегрирование)
на свою задачу, сохранив структуру и контракты. Всё, что помечено «заезд 2», включается на втором интенсиве.

## Как взять стартер себе в проект

Стартер — шаблон: его **копируют в репозиторий команды**, а не форкают и не делают своим репозиторием.
История коммитов стартера вам не нужна — ваша история начинается с коммита «стартер».

**Способ А — архив (флешка или ссылка из чата курса):**

1. Распаковать `calc-service-starter.zip`.
2. Скопировать всё содержимое папки в клон репозитория вашей команды.
   НЕ копировать: `.venv/`, `db.sqlite3`, `.env` (если успели появиться).
3. `README.md` стартера переименовать в `README_STARTER.md` — главным остаётся README вашей команды.
4. `git add . && git commit -m "стартер" && git push`. Остальные участники: `git pull`.

**Способ Б — с GitHub: https://github.com/alexshep-lab/calc-service-starter**

1. Зелёная кнопка **Code → Download ZIP** (git clone не нужен) — дальше как в способе А.

После копирования — «Быстрый старт» ниже: у каждого участника проект должен запуститься в его
собственном клоне. Обновления стартера, если будут, приедут объявлением в чат — заберёте те же
файлы поверх своих (ядро и модели это не заденет: их вы уже замените своими).

## Быстрый старт (заезд 1)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   |   source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
copy .env.example .env             # Windows   |   cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Откройте http://127.0.0.1:8000 — список задач; /tasks/new/ — форма; /api/docs — Swagger UI; /admin/ — админка.

Проверки: `pytest -q` (все тесты), `pytest core -q` (только ядро), `ruff check .` (стиль), `python -m core example_input.json` (ядро без веба).

## Структура

```
core/        вычислительное ядро: НЕ импортирует Django. run(params) -> dict, CLI, тесты на эталонах
web/         Django-приложение: модели (Task), формы, views, services.py (прикладная логика), jobs.py (очередь, заезд 2)
api/         REST API на Django Ninja: POST /api/tasks -> 202, GET /api/tasks, /api/tasks/{id}, /api/tasks/{id}/result
templates/   HTML-шаблоны (SSR + немного JS для графика и опроса статуса)
tests/       тесты API и сценария (уровни 2–3 пирамиды тестов)
warmup/      Python-выравнивание: 8 задач с тестами + шпаргалка
docs/        architecture.md (шаблон архитектурного документа), adr/ (решения)
config/      настройки Django; секреты — из .env
```

Слои и правило зависимостей: `views/api → services → core`. Ни `core`, ни `services` не знают про HTTP.

## Что делать команде

1. День 2: переименовать/расширить `Task.params` под свою задачу, заменить `core/solver.py` и `core/schemas.py`, обновить форму.
2. Межсессия 1: ядро с ≥3 тестами на эталонах, 4 эндпоинта, страницы с графиком, README, AGENTS.md, ADR-001/002.
3. Заезд 2: `USE_QUEUE=1` + `docker compose up redis` + `python manage.py rqworker` — расчёт уходит в очередь; доступ «только свои»; CI; Docker; документ.

## Заезд 2: очередь

```bash
docker compose up -d redis          # или локальный Redis
# в .env: USE_QUEUE=1
python manage.py rqworker           # в отдельном терминале
python manage.py runserver
```

Полный стек одной командой: `docker compose up --build` (веб + PostgreSQL + Redis + воркер).

## Лицензия

Учебный материал курса, А.А. Сысоев, 2026. Свободно для использования в учебных целях.

## Куда смотреть, когда застряли

- **Django по-русски:** MDN «Django» (15 частей, сквозной проект) — https://developer.mozilla.org/ru/docs/Learn_web_development/Extensions/Server-side/Django ; Django Girls Tutorial — https://tutorial.djangogirls.org/ru/
- **Django официально (англ., версия 5.2):** https://docs.djangoproject.com/en/5.2/ ; учебник — https://docs.djangoproject.com/en/5.2/intro/tutorial01/
- **Django Ninja (наш API):** https://django-ninja.dev/
- **HTTP простыми словами:** https://developer.mozilla.org/ru/docs/Web/HTTP
- **Git:** Pro Git на русском, главы 1–3 — https://git-scm.com/book/ru/v2
- **pytest:** https://docs.pytest.org/
- **Книга:** Антонио Меле, «Django 4 в примерах» (Питер, 2023).

Правило: сначала документация своей версии, потом ассистент — нейросети путают версии Django.
