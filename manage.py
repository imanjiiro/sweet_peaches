#!/usr/bin/env python
"""Утилита командной строки Django для административных задач.

Запуск сервера: python manage.py runserver
Применить миграции: python manage.py migrate
Создать миграцию: python manage.py makemigrations
Зайти в админку: python manage.py createsuperuser, затем /admin/
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не получилось импортировать Django. Убедитесь, что он "
            "установлен и виртуальное окружение активировано: "
            "pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
