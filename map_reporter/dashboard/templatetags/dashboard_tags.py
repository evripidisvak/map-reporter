from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter(name="sub")
def sub(value, arg):
    """Subtract the arg to the value."""
    if value == 0 or arg == 0:
        return "-"
    try:
        return round(float(value) - float(arg), 2)
    except (ValueError, TypeError):
        try:
            return round(value - arg, 2)
        except Exception:
            return ""

@register.filter(name="ch_sub")
def ch_sub(value, arg):
    """Find the percent change between the arg and the value."""
    if value == 0 or arg == 0:
        return "-"
    try:
        return round(((float(value) - float(arg)) / float(value) * 100), 1)
    except (ValueError, TypeError, ZeroDivisionError):
        try:
            return round(((value - arg) / value * 100),1)
        except Exception:
            return "-"

@register.filter(name="per_sub")
def per_sub(value, arg):
    """Subctract arg% from value"""
    if value == 0 or arg == 0:
        return "-"
    try:
        return round(float(value) * (1 - (float(arg) / 100)), 2)
    except (ValueError, TypeError, ZeroDivisionError):
        try:
            return round(value * (1 - (arg / 100)), 2)
        except Exception:
            return "-"

@register.filter(name="per_add")
def per_add(value, arg):
    """Add arg% in value"""
    if value == 0 or arg == 0:
        return "-"
    try:
        return round(float(value) * (1 + (float(arg) / 100)), 2)
    except (ValueError, TypeError, ZeroDivisionError):
        try:
            return round(value * (1 + (arg / 100)), 2)
        except Exception:
            return "-"


# register.filter('sub', sub)
