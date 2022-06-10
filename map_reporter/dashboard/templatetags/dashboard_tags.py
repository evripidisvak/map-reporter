from django import template
from django.contrib.auth.models import User

register = template.Library()


# def get_user(username):
#     try:
#         user = User.objects.get(username__iexact=username)
#     except User.DoesNotExist:
#         user = User.objects.none()
#     return user

# register.filter('get_user', get_user)

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

@register.filter(name="per_sub")
def per_sub(value, arg):
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


# register.filter('sub', sub)
