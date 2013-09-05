{% load deployment_tags %}

{% block wsgi %}
import os, sys

{% block path %}
sys.path = [
{% block path-before %}
{% endblock path-before %}

{% for part in sys.path %}    "{{ part|flipslash }}",
{% endfor %}

{% block path-after %}
{% endblock path-after %}
]
{% endblock path %}

{% block environ %}
os.environ["DJANGO_HOSTNAME"] = '{% if options.server_name %}{{ options.server_name }}{% elif settings.ALLOWED_HOSTS %}{{ settings.ALLOWED_HOSTS|first }}{% else %}localhost{% endif %}'
os.environ["DJANGO_SETTINGS_MODULE"] = '{{ settings.SETTINGS_MODULE }}'

{% block extra-environ %}
{% endblock extra-environ %}

{% endblock environ %}

# Additional
{% block additional %}
{% endblock additional %}

# set application for WSGI processing
{% block handler %}
from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
{% endblock handler %}

{% endblock wsgi %}
