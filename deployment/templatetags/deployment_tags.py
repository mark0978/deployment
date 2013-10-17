import importlib, os
from django import template

register = template.Library()

@register.filter(name='flipslash')
def flipslash(value):
    """ Convert all backslashes to forward slashes (for apache) """
    return value.replace("\\", '/')


@register.simple_tag
def module_path(module_name):
    assert(module_name)  # This has to be a non-empty string
    module = importlib.import_module(module_name)
    return os.path.dirname(module.__file__)
