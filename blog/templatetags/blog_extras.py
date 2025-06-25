from django import template
import math

register = template.Library()

@register.filter
def readtime(word_count):
    try:
        wc = int(word_count)
    except (ValueError, TypeError):
        return 1
    return max(1, math.ceil(wc / 200))
