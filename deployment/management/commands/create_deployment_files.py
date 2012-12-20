import os, sys
import getpass
from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from optparse import make_option
from django.conf import settings

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--prefix',
                    default=os.path.split(settings.PROJECTROOT)[1],
                    dest="prefix",
                    help='First part of the deployment file names'),
        make_option('--webserver',
                    default="apache",
                    dest="webserver",
                    help='Which webserver to create deployment files for'),
        )
    help = ("Creates deployment files for a mod_wsgi platform especially suited"
            " for apache.")


    def handle(self, *args, **options):

        wsgi_path = deploypath("%s_mod_wsgi.py" % options['prefix'])
        servertemplate = loader.get_template("deployment/%s" % webserver)
        wsgitemplate = loader.get_template("deployment/wsgi.py")
        context = {"settings": settings,
                   "sys": sys, "os": os,
                   "options": options,
                   "username": getpass.getuser(),
                   "wsgi_path": wsgi_path,}

        def deploypath(*pathparts):
            """ Create the deployment path from the PROJECT root and the passed in parts """
            return os.path.abspath(os.path.join(PROJECT_ROOT, "deploy", *pathparts))

        with open(deploypath("%s_%s" % (options['prefix'],
                                        options['webserver'])), "wt") as f:
            f.write(servertemplate.render(context))

        with open(wsgi_path, "wt")):
            f.write(wsgitemplate.render(context))