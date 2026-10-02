# REST API

Автор: Зузиева Айшат

Код: `api/api.py` (Django Ninja), подключён в `config/urls.py` как `path("api/", api.urls)`.
Документация (Swagger UI): `/api/docs`, схема OpenAPI: `/api/openapi.json`.

## Вход и доступ

* **Вход обязателен.** API использует `auth=django_auth`: тот же вход, что на страницах (`/login/`, регистрация — `/signup/`). Без входа любой адрес отвечает **401**.
* **Только свои задачи.** Задача создаётся с владельцем (`owner = request.user`). Поиск идёт по номеру И владельцу (`web/services.py`: `get_task`, `list_tasks`). Чужая задача — **404, а не 403**, и в API, и на странице `/tasks/<pk>/` (ADR-004). Чужих задач в списке нет.
* **CSRF.** Запросы, меняющие данные (`POST`), проверяются на CSRF-токен (заголовок `X-CSRFToken`, значение берётся из cookie `csrftoken`). В Swagger UI, открытом после входа, это работает автоматически.

## Адреса

| Метод | Путь | Коды | Описание |
| --- | --- | --- | --- |
| `POST` | `/api/tasks` | 202 / 401 / 403 / 422 | Создать задачу и запустить расчёт в фоне; плохие параметры — 422 с описанием ошибки, расчёт не начинается; вошёл, но запрос без CSRF-токена — 403 |
| `GET` | `/api/tasks` | 200 / 401 | Список **своих** задач (до 100); фильтр `?status=done` |
| `GET` | `/api/tasks/{id}` | 200 / 401 / 404 | Статус задачи; чужая или несуществующая — 404 |
| `GET` | `/api/tasks/{id}/result` | 200 / 401 / 404 / 409 | Результат; ещё не готов — 409; чужая — 404 |

Адреса пишутся **без «/» в конце**: `/api/tasks`, `/api/tasks/7`, `/api/tasks/7/result`.

## Что отправлять

`POST /api/tasks`, тело — JSON:

```json
{
  "name": "Утренняя смена",
  "params": {
    "doctors": 3,
    "strategy": "fifo",
    "arrival_rate": 0.15,
    "service_mean": 15.0,
    "horizon_min": 480,
    "n_runs": 100,
    "seed": 1
  }
}
```

* `name` — от 1 до 200 символов.
* `params` проверяются схемой ядра `core.schemas.SimulationParams` ДО создания задачи.

### Границы параметров

| Поле | Допустимо | Если нарушено |
| --- | --- | --- |
| `doctors` | от 1 до 20 | 422 |
| `arrival_rate` | больше 0, не больше 10 пациентов в минуту | 422 |
| `service_mean` | больше 0, не больше 240 минут | 422 |
| `horizon_min` | больше 0, не больше 1440 минут (сутки) | 422 |
| `n_runs` | от 1 до 1000 (по умолчанию 500) | 422 |
| `strategy` | `fifo`, `priority`, `dynamic` | 422 |
| `seed` | целое число или не задан | 422 |

Те же границы действуют в веб-форме (`web/forms.py` берёт числа из `core/schemas.py`) и в ядре: проверка одна, расходиться ей не с чем.

## Ответы

`202 Accepted` на создание — расчёт принят, а не готов:

```json
{"id": 7, "name": "Утренняя смена", "status": "created", "core_version": "", "error": ""}
```

`GET /api/tasks/7/result`, когда расчёт готов:

```json
{"id": 7, "status": "done", "result": {"average_wait_time": 4.2, "max_wait_time": 31.0, "average_queue_length": 0.6, "doctor_utilization": 0.71, "served_patients_count": 70, "wait_times": [0.0, 1.5], "core_version": "1.0.0", "elapsed_sec": 0.01}}
```

Статусы задачи: `created → running → done / failed`; в режиме очереди RQ (`USE_QUEUE=1`) добавляется `queued`. Если расчёт упал, в поле `error` — причина.

Ошибки приходят как `{"detail": "..."}`.
