# movies/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def translate_role(value):
    role_translations = {
        'Director': 'Режиссер',
        'Writer': 'Сценарист',
        'Producer': 'Продюсер',
        'Actor': 'Актер',
        'Composer': 'Композитор',
        'Cinematographer': 'Оператор',
    }
    return role_translations.get(value, value)