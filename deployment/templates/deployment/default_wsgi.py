{% load deployment_tags %}import os, sys

sys.path = [
{% for part in sys.path %}    "{{ part|flipslash }}",
{% endfor %}
]

os.environ["DJANGO_HOSTNAME"] = '{% if options.server_name %}{{ options.server_name }}{% elif settings.ALLOWED_HOSTS %}{{ settings.ALLOWED_HOSTS|first }}{% else %}localhost{% endif %}'
os.environ["DJANGO_SETTINGS_MODULE"] = '{{ settings.SETTINGS_MODULE }}'

# set application for WSGI processing
from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
