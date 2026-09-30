# Hospital Flow Simulation

## Идея проекта

Моделируем поток пациентов в приёмном отделении больницы: как они поступают, сколько ждут в очереди и как их обслуживают врачи. Задача — сравнить стратегии выбора пациента из очереди (FIFO, Priority, Dynamic) и найти ту, что меньше всего заставляет людей ждать.

---

## Как работает система

```
Пациенты поступают (пуассоновский поток)
        ↓
Формируется очередь (куча heapq)
        ↓
Врач берёт пациента по стратегии (FIFO / Priority / Dynamic)
        ↓
Пациент обслуживается
        ↓
Считаются метрики, результат сохраняется в Task.result (JSON)
```

Вычислительное ядро (`core/solver.py`) не зависит от Django. Оно умеет два режима: детерминированный (готовый список пациентов, для эталонных тестов) и случайный (поток пациентов с экспоненциальным временем приёма).

Расчёт запускается с веб-формы `/` или через API (`POST /api/tasks`) и выполняется **в фоне** через `threading.Thread`, не блокируя веб-сервер. Вместо потоков можно включить очередь RQ + Redis флагом `USE_QUEUE=1`.

---

## Эталонные тесты

**Эталон 1 (FIFO).** 1 врач, 3 пациента в момент `t = 0` (приём по 5 мин). Ожидание: `[0.0, 5.0, 10.0]`, среднее `5.0` мин, обслужено `3`. Ручной расчёт: `(0 + 5 + 10) / 3 = 5.0`.

**Эталон 2 (теория очередей M/M/1).** 1 врач, 0.1 пациента в минуту, приём в среднем 5 минут, смена 5000 минут, 200 прогонов. Загрузка `ρ = 0.1 · 5 = 0.5`, средняя длина очереди `Lq = ρ² / (1 − ρ) = 0.5` человека. Тест проверяет диапазон `0.4 … 0.6` (результат случайный).

**Средняя длина очереди** считается как сумма времён ожидания всех пациентов (человеко-минуты), делённая на длину смены `max_time`: получаем, сколько человек в среднем стояло в очереди. Это не доля принятых пациентов (так было раньше, и поле всегда равнялось 1.0).

Тесты ядра: `core/tests/test_solver.py`. Тесты API и фоновой работы: `tests/`.

---

## Случайность и воспроизводимость

В `generate_stochastic_patients` у каждого вызова **свой генератор** `rng = random.Random(seed)`. Общий `random.seed(...)` не используется: две задачи в разных потоках одновременно мешали бы друг другу, и один и тот же `seed` давал бы разные ответы. Теперь тот же `seed` всегда даёт тот же результат, а глобальный `random` ядро не трогает (тесты `test_same_seed_same_result`, `test_global_random_is_not_touched`).

---

## Замер скорости

Условия: 3 врача, смена 480 мин, один прогон (`n_runs=1`, `seed=1`), перегрузка. Время в секундах, компьютер разработчика, значения ориентировочные.

| Стратегия | Поток, пац/мин | Пациентов | Было (`max()` по очереди) | Стало (`heapq`) |
| --- | --- | --- | --- | --- |
| fifo | 1 | 455 | 0.00 | 0.00 |
| fifo | 10 | 4 745 | 0.06 | 0.02 |
| fifo | 40 | 19 170 | 0.67 | 0.06 |
| priority | 1 | 455 | 0.01 | 0.00 |
| priority | 10 | 4 745 | 1.07 | 0.03 |
| priority | 40 | 19 170 | 21.35 | 0.07 |
| dynamic | 1 | 455 | 0.01 | 0.00 |
| dynamic | 10 | 4 745 | 2.93 | 0.02 |
| dynamic | 40 | 19 170 | 42.46 | 0.07 |

**Вывод.** На малом входе (1 пац/мин) разницы не видно. На входе ×4 время у `priority` и `dynamic` росло примерно в 20 раз — рост близок к квадрату, потому что `max()` для каждого пациента проходил всю очередь: `n` пациентов × очередь длины `n` = `n²`. Куча достаёт лучшего за `log n` шагов, всего `n · log n`; порядок приёма при этом не изменился (результаты совпадают со старым кодом на всех проверенных потоках и стратегиях).

**Про стратегию dynamic.** Счёт `приоритет + (t − приход) / 15` равен `(приоритет − приход / 15) + t / 15`. Слагаемое `t / 15` одинаково у всех в очереди, поэтому порядок пациентов задаётся в момент прихода и не меняется со временем. «Динамическая» стратегия со старением на деле статическая. Это свойство формулы, а не ошибка; по-настоящему динамической она станет, если вес ожидания будет зависеть от приоритета.

---

## Входные данные и параметры

**Параметры веб-формы (`TaskForm`):**

* Количество врачей (`doctors`: от 1 до 20, по умолчанию `3`);
* Интенсивность прихода (`arrival_rate`: пац/мин, по умолчанию `0.15`);
* Среднее время приёма (`service_mean`: мин, по умолчанию `15.0`);
* Длительность смены (`horizon_min`: мин, по умолчанию `480.0` — 8 часов);
* Стратегия очереди (`strategy`: `fifo`, `priority`, `dynamic`).

Через API и ядро доступны также `n_runs` (число прогонов, 1–1000, по умолчанию 500), `seed` и готовый список `patients`. Значения по умолчанию в схеме ядра (`core/schemas.py`) другие: `arrival_rate = 1.0`, `service_mean = 5.0`, `doctors = 1`.

---

## Фоновая обработка

Расчёт выполняется асинхронно через `threading.Thread`: `web/services.py`, функция `create_task` запускает поток, функция `execute_task` выполняет расчёт. Клиент сразу получает `HTTP 202 Accepted`.

Статус задачи в режиме потоков: `created → running → done / failed`. Статус `queued` появляется только в режиме очереди RQ (`USE_QUEUE=1`, `web/jobs.py`).

Каждый фоновый поток закрывает соединения с БД через `connections.close_all()`. Страница задачи (`templates/web/detail.html`) опрашивает `/api/tasks/{id}` раз в 1,5 секунды.

**Перезапуск.** Потоки `daemon=True` обрываются вместе с процессом: задача в статусе `running` навсегда остаётся «считается». Подробнее — `docs/adr/002-async-threads.md`.

---

## Структура проекта

```
manage.py
config/                 — настройки Django (settings, urls, wsgi)
core/                   — вычислительное ядро (без зависимостей от Django)
  solver.py             — симуляция: очередь на куче heapq, свой генератор rng
  schemas.py            — Pydantic-схемы входа и выхода
  tests/                — тесты ядра (эталоны, M/M/1, seed, порядок кучи)
api/
  api.py                — REST API на Django Ninja, доступ только к своим задачам
web/                    — Django-приложение
  models.py             — модель Task
  forms.py              — форма TaskForm
  views.py              — HTML-представления
  services.py           — create_task / execute_task, фоновые потоки
  jobs.py               — очередь RQ (режим USE_QUEUE=1)
  admin.py, urls.py, migrations/, management/commands/rqworker.py
templates/              — base.html, web/list.html, web/form.html, web/detail.html
tests/                  — тесты API, фонового запуска и сценария
warmup/                 — учебная разминка (запускается отдельно: pytest warmup)
docs/
  architecture.md       — архитектурный документ (12 разделов)
  ER.png                — ER-диаграмма (User 0..1 — ∞ Task)
  fat_review.md         — разбор «толстой» функции
  adr/                  — 000-template, 001-stack, 002-async-threads, 003-storage-json
.github/workflows/python-app.yml — CI (pytest)
Dockerfile, docker-compose.yml   — запуск в Docker (web, worker, db, redis)
AGENTS.md, README_STARTER.md, example_input.json, pytest.ini, pyproject.toml, requirements.txt
```

---

## REST API

Swagger: `/api/docs`.

| Метод | Путь | Коды | Описание |
| --- | --- | --- | --- |
| `POST` | `/api/tasks` | 202 / 422 | Создать задачу и запустить расчёт; плохие параметры — 422 |
| `GET` | `/api/tasks` | 200 | Список **своих** задач; без входа — только анонимные |
| `GET` | `/api/tasks/{id}` | 200 / 404 | Статус задачи |
| `GET` | `/api/tasks/{id}/result` | 200 / 404 / 409 | Результат; ещё не готов — 409 |

**Доступ.** Чужая задача (и статус, и результат) — **404, а не 403**: посторонний не должен знать, что задача с таким номером есть. На странице (`/tasks/<pk>/`) для чужой задачи остаётся 403.

---

## Быстрый запуск

1. **Установка:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Миграции и сервер:**
```bash
python manage.py migrate
python manage.py runserver
```

3. **Тесты:**
```bash
pytest -q
```

* Веб-интерфейс: http://127.0.0.1:8000/
* Документация API: http://127.0.0.1:8000/api/docs

**Очередь RQ и Docker:** `docker compose up --build` поднимает web, worker, PostgreSQL и Redis (`USE_QUEUE=1`).

---

## Документация

* [`docs/architecture.md`](docs/architecture.md) — архитектурный документ.
* [`docs/ER.png`](docs/ER.png) — ER-диаграмма базы данных (`User` и `Task`).
* [`docs/adr/001-stack.md`](docs/adr/001-stack.md) — ADR-001: стек (Django + Django Ninja).
* [`docs/adr/002-async-threads.md`](docs/adr/002-async-threads.md) — ADR-002: фоновые потоки `threading.Thread`.
* [`docs/adr/003-storage-json.md`](docs/adr/003-storage-json.md) — ADR-003: хранение результатов в `JSONField`.
* [`docs/fat_review.md`](docs/fat_review.md) — разбор «толстой» функции.

---

## Команда

* Умалатова Айна (fakandar)
* Зузиева Айшат (zuzievwa)
* Муцалова Иман (imanjiiro)


### Вклад участников

| Участник | Вклад в проект |
| --- | --- |
| **Умалатова Айна**| База данных и серверная часть: `core/schemas.p`, `core/__init__.py`, `core/__main__.py`, `web/models.py`, `web/migrations/`, `web/services.py`, `web/jobs.py`, `web/management/`, `web/apps.py`, `web/__init__.py`, `config/settings.py`, `config/wsgi.py`, `config/__init__.py`, `manage.py`, `docs/ER.png`|
|**Зузиева Айшат**| Расчёты, API, веб-страницы и архитектура: `core/solver.py`, `api/`, `web/views.py`, `web/forms.py`, `web/admin.py`, `web/urls.py`, `web/views_fat_example.py`, `config/urls.py`, `templates/`, `example_input.json`, `docs/architecture.md`, `docs/fat_review.md`, `docs/adr/`|
|**Муцалова Иман**| Тесты, CI, Docker и документация: `core/tests/`, `tests/`, `.github/workflows/python-app.yml`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `pytest.ini`, `pyproject.toml`, `.gitignore`, `README.md`, `README_STARTER.md`, `AGENTS.md`, `warmup/`  |