from django import template
from transliterate import translit

register = template.Library()

@register.filter
def translit_slug(value):
    print(f"translit_slug called with value: '{value}'")
    transliterated = translit(value.lower(), 'ru', reversed=True)
    slug = ''.join(c if c.isalnum() else '-' for c in transliterated).strip('-')
    print(f"translit_slug result: '{slug}'")
    return slug

@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)