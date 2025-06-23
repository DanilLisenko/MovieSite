import os
import sys
import json
import django
from django.core.management import call_command

# Указываем путь к модулю настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')

# Инициализируем Django
django.setup()

# Открываем файл с кодировкой UTF-8 и перенаправляем вывод
with open('data.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', stdout=f)