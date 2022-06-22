from django import template
from django.contrib.auth.models import User
from django.template.base import Node
from django.utils.functional import keep_lazy as allow_lazy
import six, os
from mimetypes import guess_type
from base64 import b64encode
# from django.contrib.staticfiles import finders

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

@register.tag
def linebreakless(parser, token):
    nodelist = parser.parse(('endlinebreakless',))
    parser.delete_first_token()
    return LinebreaklessNode(nodelist)


class LinebreaklessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        strip_line_breaks = allow_lazy(lambda x: x.replace('\n', ''), six.text_type)
        return strip_line_breaks(self.nodelist.render(context).strip())

# register.filter('sub', sub)


@register.filter
def datalize(filename, content_type=None):
    """
    This filter will return data URI for given file, for more info go to:
    http://en.wikipedia.org/wiki/Data_URI_scheme
    Sample Usage:
    <img src="{{ 'image.jpg'|datalize }}"/> or 
    <img src="{% static 'image.jpg'|datalize %}"/>
    will be filtered into:
    <img src="data:image/png;base64,iVBORw0...">
    """
    if filename:
        #we do this because FUCKIN windows..
        filename = filename.replace('/','',1).replace('/','\\')
        with open(filename, "rb") as f:
            data = f.read()

        encoded = b64encode(data)
        content_type, encoding = guess_type(filename)
        return "data:%s;base64,%s" % (content_type, encoded.decode('utf-8'))
    else:
        return ''