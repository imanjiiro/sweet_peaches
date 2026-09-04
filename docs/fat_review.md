# fat_review.md — разбор «толстой» функции

## Пример «толстой» функции (как НЕ надо)

Вот как выглядела бы вьюха, если бы мы (по привычке) запихнули в неё
всё сразу — приём формы, валидацию, расчёт и сохранение:

```python
# web/views.py — ПЛОХОЙ вариант, для разбора, в проекте так не делаем
def create_run_bad(request):
    num_doctors = int(request.POST["num_doctors"])
    patient_rate = float(request.POST["patient_rate"])
    service_time_mean = float(request.POST["service_time_mean"])
    strategy = request.POST["strategy"]

    if num_doctors <= 0 or patient_rate <= 0 or service_time_mean <= 0:
        return HttpResponseBadRequest("bad params")

    # "тяжёлая" симуляция прямо внутри вьюхи, синхронно
    import random
    wait_times = []
    doctors_free_at = [0.0] * num_doctors
    t = 0.0
    for _ in range(20000):
        t += random.expovariate(patient_rate / 60)
        i = doctors_free_at.index(min(doctors_free_at))
        start = max(t, doctors_free_at[i])
        wait_times.append(start - t)
        doctors_free_at[i] = start + random.expovariate(1 / service_time_mean)

    run = SimulationRun.objects.create(
        num_doctors=num_doctors, patient_rate=patient_rate,
        service_time_mean=service_time_mean, strategy=strategy, status="done",
    )
    SimulationResult.objects.create(
        run=run,
        avg_wait_time=sum(wait_times) / len(wait_times),
        patients_served=len(wait_times),
    )
    return redirect("web:list")
```

## Проблемы (минимум 5) и в какой слой каждую уводить

1. **Разбор и валидация входных данных сделаны вручную (`int(request.POST[...])`).**
   Нет единой точки, где проверяются границы (`num_doctors > 0` и т.д.) —
   легко забыть проверку в одном из мест, если таких вьюх станет больше.
   → **Куда уехать:** в `web/forms.py` (`SimulationRunForm`, `ModelForm`)
   — валидация уже вынесена туда в нашем реальном коде.

2. **Вычислительная логика (сама симуляция) написана прямо внутри вьюхи.**
   Её нельзя протестировать без Django, без HTTP и без БД — придётся
   поднимать весь веб-стек ради теста одной формулы.
   → **Куда уехать:** в `core/simulation.py` — модуль, который не знает
   ни про Django, ни про HTTP, и тестируется отдельно
   (`core/tests/test_simulation_reference.py`).

3. **Вьюха синхронно ждёт результат тяжёлого расчёта (20 000 итераций) внутри одного HTTP-запроса.**
   Пользователь смотрит на «крутилку» браузера, пока сервер молча
   считает; при росте `num_patients` запрос рискует упереться в таймаут.
   → **Куда уехать:** расчёт — в фоновую задачу (см. `ADR-001`), вьюха
   только создаёт запись со статусом `queued` и сразу отвечает.

4. **Смешаны два уровня ответственности: сохранение в БД и математика.**
   Функция одновременно и «считает очередь», и «пишет в SimulationRun/
   SimulationResult» — если завтра появится второй способ запускать
   расчёт (например, из management-команды или из API), код придётся
   дублировать или копипастить вьюху целиком.
   → **Куда уехать:** сохранение — остаётся в `web/` (модели уже есть),
   а связующий код («вызвать core, полученные метрики положить в
   модели») стоит вынести в отдельную функцию `web/services.py`, чтобы
   и вьюха, и будущий API-эндпоинт звали одну и ту же функцию.

5. **Импорт `random` спрятан внутри функции, и нет `rng_seed`.**
   Результат не воспроизводим — нельзя перезапустить тот же расчёт и
   получить тот же ответ, а значит нельзя написать детерминированный
   тест на конкретные числа (только на диапазоны).
   → **Куда уехать:** параметр `rng_seed` — часть публичного интерфейса
   `core/simulation.py` (уже добавлен в реальном коде), а не случайное
   зерно, зашитое внутри функции.

6. *(бонус)* **Нет обработки ошибок расчёта.**
   Если внутри цикла вылетит исключение (например, `service_time_mean`
   окажется отрицательным, несмотря на форму), пользователь получит
   голый 500 без объяснений, а запись в БД не создастся вообще —
   он даже не увидит, что что-то пошло не так.
   → **Куда уехать:** обработка ошибок — на границе `web/services.py`,
   которая ловит ошибки ядра и переводит прогон в статус `failed`
   вместо падения всего запроса.
