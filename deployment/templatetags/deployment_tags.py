from django import template

register = template.Library()

@register.filter(name='flipslash')
def flipslash(value):
    """ Convert all backslashes to forward slashes (for apache) """
    return value.replace("\\", '/')
