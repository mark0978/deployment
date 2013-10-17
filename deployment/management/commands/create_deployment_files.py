import os, sys, re
import getpass

import django
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.template import loader, Context
from optparse import make_option
from django.conf import settings

from ...models import SettingsModule, CommandLine

try:
    PROJECT_NAME = settings.SETTINGS_MODULE.split('.')[1]
except IndexError:
    PROJECT_NAME = ""

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--file-prefix',
                    default=PROJECT_NAME,
                    dest="prefix",
                    help='First part of the deployment file names, {prefix}_{webserver}.vhost and {prefix}_wsgi.py'),
        make_option('--webserver',
                    default="apache",
                    dest="webserver",
                    help='Which webserver to create deployment files for [apache|nginx], defaults to apache.  Used in picking the vhost template'),
        make_option('--server-admin',
                    default=settings.ADMINS[0][1],
                    dest="server_admin",
                    help='Email address of the server admin for the vhost file'),
        make_option('--processes',
                    default=5,
                    dest="processes",
                    help='Number of processes to run, ignored for windows'),
        make_option('--threads',
                    default=5,
                    dest="threads",
                    help='Number of threads per process, ignored for windows'),
        make_option('--server-name',
                    default=None,
                    dest="server_name",
                    help="Don't use this with Django >1.4, settings.ALLOWED_HOSTS will be automatically used."\
                        "For older versions, the name of the host for virtual host setups"),
        make_option('--output-dir',
                    default=None,
                    dest="output_dir",
                    help="Name of the directory to write the deployment files in."),
        make_option('--ssl-dir',
                    default=None,
                    dest="ssl_dir",
                    help="Name of the directory that contains your ssl key, cert and option ca cert files "),
        )
    help = ("\nCreates deployment files for a wsgi platform based on"
            " templates in the deployment templates folder.\n")


    def find_ssl_files(self, dirname):
        """ Scans dirname for files that look like certificate files to fill out the ssl
        portion of the vhost file """
        data = {}
        if dirname:
            re_key = re.compile(".+\\.key$")
            re_cert = re.compile(".+\\.(cert|crt)$")
            re_cacert = re.compile(".+\\.(ca\\.crt|ca\\.cert|ca-bundle)")
            if dirname:
                files = os.listdir(dirname)
                for f in files:
                    if re_key.match(f):
                        data["keyfile"] = os.path.abspath(os.path.join(dirname, f))
                    elif re_cacert.match(f):
                        data["cacertfile"] = os.path.abspath(os.path.join(dirname, f))
                    elif re_cert.match(f):
                        data["certfile"] = os.path.abspath(os.path.join(dirname, f))

            #print "files=", files
            #print "ssl=",data
        return data

    def handle(self, *args, **options):

        if not args:
            module = SettingsModule.objects.get(name=os.environ['DJANGO_SETTINGS_MODULE'])
            cmdline = CommandLine.objects.filter(module=module).latest('when')

            args = cmdline.arguments
            options = {}
            for key, value in cmdline.options.items():
                if value:
                    options[key] = value


            print "Creating deployment files with %s and %s" % (args, options)

        else:
            module = SettingsModule.objects.get_or_create(name=os.environ['DJANGO_SETTINGS_MODULE'])[0]
            cmdline = CommandLine(command="create_deployment_files", module=module, arguments=args,
                                  options=options)
            cmdline.save()

        self.do_work(*args, **options)

    def do_work(self, *args, **options):
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
            wsgitemplate = loader.select_template(["deployment/wsgi.pytemplate",
                                                   "deployment/default_wsgi.pytemplate"])

            if options.get("ssl_dir", None) and not os.path.isdir(options["ssl_dir"]):
                raise CommandError('%s is not a directory' % options["ssl_dir"])

            context = Context({"settings": settings,
                               "sys": sys, "os": os,
                               "options": options,
                               "username": getpass.getuser(),
                               "wsgi_path": wsgi_path,
                               "ssl": self.find_ssl_files(options.get("ssl_dir", None)),
                               },
                              autoescape=False)

            if not settings.ALLOWED_HOSTS and django.get_version() >= '1.4.4':
                raise CommandError("settings.ALLOWED_HOSTS is empty, this is not going to go so well")

            def white_smush(intxt):
                txt = re.sub('[\t ]*\r', '', intxt)
                txt = re.sub('\n\n+', '\n', txt)
                return re.sub('========+', '\n', txt)

            def undent(intxt):
                return re.sub('\n +', '\n    ', intxt)

            with open(server_path, "wt") as f:
                f.write(undent(white_smush(servertemplate.render(context))))
                print "Wrote server vhost in %s" % server_path

            with open(wsgi_path, "wt") as f:
                f.write(white_smush(wsgitemplate.render(context)))
                print "Wrote wsgi script in %s" % wsgi_path

            #print options
