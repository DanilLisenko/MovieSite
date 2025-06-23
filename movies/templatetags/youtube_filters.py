from django import template
import re

register = template.Library()

@register.filter
def youtube_embed_url(value):
    """
    Преобразует YouTube URL в формат для встраивания.
    Поддерживает форматы:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    if not value:
        return ""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)",
        r"(?:youtube\.com/.*v=)([a-zA-Z0-9_-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}?rel=0"
    return ""