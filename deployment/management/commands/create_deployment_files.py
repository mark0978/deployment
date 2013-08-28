import os, sys
import getpass
from django.core.management.base import BaseCommand, CommandError
from django.template import loader, Context
from optparse import make_option
from django.conf import settings

PROJECT_NAME = settings.SETTINGS_MODULE.split('.')[0]

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--file-prefix',
                    default=PROJECT_NAME,
                    dest="prefix",
                    help='First part of the deployment file names, {prefix}_{webserver}.vhost and {prefix}_wsgi.py'),
        make_option('--webserver',
                    default="apache",
                    dest="webserver",
                    help='Which webserver to create deployment files for, [apache or nginx]'),
        make_option('--server-admin',
                    default=settings.ADMINS[0][1],
                    dest="server_admin",
                    help='Email address of the server admin for the vhost file'),
        make_option('--processes',
                    default=5,
                    dest="processes",
                    help='Number of processes to run'),
        make_option('--threads',
                    default=5,
                    dest="threads",
                    help='Number of threads per process'),
        make_option('--server-name',
                    default=None,
                    dest="server_name",
                    help="Don't use this with Django >1.4, settings.ALLOWED_HOSTS will be automatically used."\
                        "For older versions, the name of the host for virtual host setups"),
        make_option('--output-dir',
                    default=None,
                    dest="output_dir",
                    help="Name of the directory to write the deployment files in."),
        )
    help = ("Creates deployment files for a mod_wsgi platform based on"
            " templates in the deployment templates folder.")


    def handle(self, *args, **options):

        # Flesh out options with the name=value pairs from the command line
        for arg in args:
            if "=" in arg:
                name, value = arg.split('=')
                if name in options:
                    oldvalue = options[name]
                    if isinstance(oldvalue, list):
                        oldvalue.append(value)
                    else:
                        options[name] = [oldvalue, value]
                else:
                    options[name] = [value]
            # ignore those that don't have an equal in the string

        # Not done in the options, so I can put the abspath on it
        output_dir = options["output_dir"]
        if output_dir:
            output_dir = os.path.abspath(output_dir)
        else:
            output_dir = os.path.abspath(os.path.join(settings.PROJECT_ROOT, "deploy"))

        wsgi_path = os.path.join(output_dir, "%s_wsgi.py" % options['prefix'])
        server_path = os.path.join(output_dir, "%s_%s.vhost" % (options['prefix'], options['webserver']))

        servertemplate = loader.select_template(["deployment/%s" % options['webserver'],
                                                 "deployment/default_%s" % options['webserver']])
        wsgitemplate = loader.select_template(["deployment/wsgi.py",
                                               "deployment/default_wsgi.py"])
        context = Context({"settings": settings,
                           "sys": sys, "os": os,
                           "options": options,
                           "username": getpass.getuser(),
                           "wsgi_path": wsgi_path, },
                          autoescape=False)

        if not settings.ALLOWED_HOSTS:
            sys.stderr.write("settings.ALLOWED_HOSTS is empty, this is not going to go so well")

        with open(server_path, "wt") as f:
            f.write(servertemplate.render(context))
            print "Wrote server vhost in %s" % server_path

        with open(wsgi_path, "wt") as f:
            f.write(wsgitemplate.render(context))
            print "Wrote wsgi script in %s" % wsgi_path

        #print options
