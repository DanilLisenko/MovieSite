# movies/templatetags/youtube_tags.py
from django import template
import re

register = template.Library()

@register.filter
def urlize_youtube(value):
    # Извлекаем VIDEO_ID из ссылки
    match = re.search(r'(?:v=)([A-Za-z0-9_-]+)', value)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    return value