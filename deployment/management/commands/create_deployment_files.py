import os, sys, re, importlib, optparse
import getpass

import django
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.template.backends.django import Engine
from django.template import Context
from optparse import make_option
from django.conf import settings

from ...models import SettingsModule, CommandLine

try:
    PROJECT_NAME = settings.SETTINGS_MODULE.split('.')[1]
except IndexError:
    PROJECT_NAME = ""

def safe_mkdir(dirname):
    """ Create dirname if it doesn't exist.  If it does, just return, any other error passes the
          exception to the caller to deal with. (or not)"""
    try:
        os.mkdir(dirname)
    except FileExistsError:
        pass

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--use-previous',
                            default=False,
                            action="store_true",
                            dest="use_previous",
                            help='Use previous settings to regenerate the deployment files.'),
        parser.add_argument('--file-prefix',
                            default=PROJECT_NAME,
                            dest="prefix",
                            help='First part of the deployment file names, {prefix}_{webserver}.vhost and {prefix}_wsgi.py'),
        parser.add_argument('--webserver',
                            default="apache",
                            dest="webserver",
                            help='Which webserver to create deployment files for [apache|nginx], defaults to apache.  Used in picking the vhost template'),
        parser.add_argument('--server-admin',
                            default=settings.ADMINS[0][1],
                            dest="server_admin",
                            help='Email address of the server admin for the vhost file'),
        parser.add_argument('--processes',
                            default=5,
                            dest="processes",
                            help='Number of processes to run, ignored for windows'),
        parser.add_argument('--threads',
                            default=5,
                            dest="threads",
                            help='Number of threads per process, ignored for windows'),
        parser.add_argument('--output-dir',
                            default=None,
                            dest="output_dir",
                            help="Name of the directory to write the deployment files in, defaults to the settings module dir/deploy"),
        parser.add_argument('--ssl-dir',
                            default=None,
                            dest="ssl_dir",
                            help="Name of the directory that contains your ssl key, cert and option ca cert files "),
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

                if len(data) == 0:
                    # Lets Encrypt maybe?
                    # cert.pem       chain.pem      fullchain.pem  privkey.pem
                    self.stdout.write("Trying LetsEncrypt Keys instead\n")
                    re_key = re.compile("^privkey.pem$")
                    re_cert = re.compile("^cert.pem$")
                    re_cacert = re.compile("^fullchain.pem$")
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

    def _remove_defaults(self, options):
        """ Return a dict of the options that are NOT default """
        opts = {}
        for option in Command.option_list:
            if ((optparse.NO_DEFAULT == option.default and options[option.dest])
                or (optparse.NO_DEFAULT != option.default
                    and option.default != options[option.dest])):
                opts[option.dest] = options[option.dest]

        return opts

    def cmdline(self, args, options):
        """ Format the options as as string to print out """
        arguments = []
        cleanopts = self._remove_defaults(options)
        for option in Command.option_list:
            if option.dest in cleanopts:
                if option.takes_value():
                    argument = "%s=%s" % (option.get_opt_string(), cleanopts[option.dest])
                else:
                    argument = option.get_opt_string()
                if " " in argument:
                    argument = "'%s'" % argument

                arguments.append(argument)

        return " ".join(arguments)

    def handle(self, *args, **options):

        save_cmdline = False
        if options.get('use_previous', False):
            try:
                module = SettingsModule.objects.get(name=os.environ['DJANGO_SETTINGS_MODULE'])
            except SettingsModule.DoesNotExist:
                raise CommandError("No saved settings to create deployment files with, please "\
                                   "specify your options")
            cmdline = CommandLine.objects.filter(module=module).latest('when')

            # Hopefully the same name=value pair will overwrite the previous one
            cmdline.arguments += list(args)

            cmdline.options.update(self._remove_defaults(options))

            # This is not completely accurate, revisit at a later point
            self.stdout.write("Invoking as if you used:\n%s\n" 
                              % self.cmdline(cmdline.arguments, cmdline.options))

            if len(sys.argv) > 3:
                del cmdline.options['use_previous']
                args = cmdline.arguments
                options = cmdline.options
                save_cmdline = True

        else:
            save_cmdline = True

        if save_cmdline:
            module = SettingsModule.objects.get_or_create(name=os.environ['DJANGO_SETTINGS_MODULE'])[0]
            cmdline = CommandLine.objects.create(command="create_deployment_files", module=module,
                                                 arguments=list(args), options=options)

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
                settings_module = importlib.import_module(os.environ['DJANGO_SETTINGS_MODULE'])
                output_dir = os.path.abspath(os.path.join(os.path.dirname(settings_module.__file__), "deploy"))

            wsgi_path = os.path.join(output_dir, "%s_wsgi.py" % options['prefix'])
            server_path = os.path.join(output_dir, "%s_%s.vhost" % (options['prefix'], options['webserver']))

            engine = Engine(dirs=settings.TEMPLATES[0]['DIRS'], 
                            app_dirs=True, debug=settings.DEBUG, autoescape=False,
                            libraries={'deployment_tags': 'deployment.templatetags.deployment_tags'})

            servertemplate = engine.select_template(["deployment/%s" % options['webserver'],
                                                     "deployment/default_%s" % options['webserver']])
            wsgitemplate = engine.select_template(["deployment/wsgi.pytemplate",
                                                   "deployment/default_wsgi.pytemplate"])

            if options.get("ssl_dir", None) and not os.path.isdir(options["ssl_dir"]):
                raise CommandError('%s is not a directory' % options["ssl_dir"])

            using_ssl = self.find_ssl_files(options.get("ssl_dir", None))
            if using_ssl and not settings.SESSION_COOKIE_SECURE:
                raise CommandError("Trying to use ssl without settings.SESSION_COOKIE_SECURE is a"
                                   "bad idea.  Go fish!")

            context = Context({"settings": settings,
                       "sys": sys, "os": os,
                       "options": options,
                       "username": getpass.getuser(),
                       "wsgi_path": wsgi_path,
                       "ssl": using_ssl,
                       }, autoescape=False)

            if not settings.ALLOWED_HOSTS and django.get_version() >= '1.4.4':
                raise CommandError("settings.ALLOWED_HOSTS is empty, this is not going to go so well")

            def white_smush(intxt):
                txt = re.sub('[\t ]*[\r\n]', '\n', intxt)
                txt = re.sub('\n\n+', '\n', txt)
                return re.sub('========+', '\n', txt)

            def undent(intxt):
                return re.sub('\n +', '\n    ', intxt)

            safe_mkdir(os.path.dirname(server_path))
            with open(server_path, "wt") as f:
                f.write(undent(white_smush(servertemplate.render(context))))
                self.stdout.write("Wrote server vhost in %s\n" % server_path)


            safe_mkdir(os.path.dirname(wsgi_path))
            with open(wsgi_path, "wt") as f:
                f.write(white_smush(wsgitemplate.render(context)))
                self.stdout.write("Wrote wsgi script in %s\n" % wsgi_path)

            #print options
