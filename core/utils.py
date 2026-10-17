import math
import re

from django.utils.text import slugify
from rest_framework.throttling import BaseThrottle


def unique_slug(model, value, fallback="item", max_length=200):
    base = (slugify(value) or fallback)[:max_length]
    slug, n = base, 2
    while model.objects.filter(slug=slug).exists():
        suffix = f"-{n}"
        slug = f"{base[:max_length - len(suffix)]}{suffix}"
        n += 1
    return slug


def client_ip(request):
    return BaseThrottle().get_ident(request)   # honours NUM_PROXIES


def reading_time_minutes(text):
    words = len(re.findall(r"\w+", text or ""))
    return max(1, math.ceil(words / 200))