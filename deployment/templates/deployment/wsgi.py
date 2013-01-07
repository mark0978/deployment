import os, sys

sys.path = [
{% for part in sys.path %}    "{{ part }}",
{% endfor %}
]

from django.core.handlers.wsgi import WSGIHandler
#import pinax.env

#setup the environment for Django and Pinax
#pinax.env.setup_environ(__file__, settings_path=os.path.abspath(os.path.join()

{% if options.servername %}
os.environ["DJANGO_HOSTNAME"] = {{ options.servername }}.split('.')[0]
{% endif %}
os.environ["DJANGO_SETTINGS_MODULE"] = '{{ settings.SETTINGS_MODULE }}'

# set application for WSGI processing
application = WSGIHandler()
