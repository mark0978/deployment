import os, sys
import getpass
from django.core.management.base import BaseCommand, CommandError
from django.template import loader, Context
from optparse import make_option
from django.conf import settings

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--prefix',
                    default=settings.SETTINGS_MODULE.split('.')[0],
                    dest="prefix",
                    help='First part of the deployment file names'),
        make_option('--webserver',
                    default="apache",
                    dest="webserver",
                    help='Which webserver to create deployment files for'),
        make_option('--server_admin',
                    default=settings.ADMINS[0][1],
                    dest="server_admin",
                    help='Email address of the server admin'),
        make_option('--processes',
                    default=5,
                    dest="processes",
                    help='Number of processes to run'),
        make_option('--threads',
                    default=5,
                    dest="threads",
                    help='Number of threads per process'),
        )
    help = ("Creates deployment files for a mod_wsgi platform based on"
            " templates in the deployment templates folder.")


    def handle(self, *args, **options):

        def deploypath(*pathparts):
            """ Create the deployment path from the PROJECT root and the passed in parts """
            return os.path.abspath(os.path.join(settings.PROJECT_ROOT,
                                                "deploy", *pathparts))

        wsgi_path = deploypath("%s_wsgi.py" % options['prefix'])
        server_path = deploypath("%s_%s" % (options['prefix'], options['webserver']))

        servertemplate = loader.get_template("deployment/%s" % options['webserver'])
        wsgitemplate = loader.get_template("deployment/wsgi.py")
        context = Context({"settings": settings,
                           "sys": sys, "os": os,
                           "options": options,
                           "username": getpass.getuser(),
                           "wsgi_path": wsgi_path, },
                          autoescape=False)

        with open(server_path, "wt") as f:
            f.write(servertemplate.render(context))
            print "Wrote server config in %s" % server_path

        with open(wsgi_path, "wt") as f:
            f.write(wsgitemplate.render(context))
            print "Wrote wsgi script in %s" % wsgi_path
