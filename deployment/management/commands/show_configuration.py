import os, sys, pprint

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings

PROJECT_NAME = settings.SETTINGS_MODULE.split('.')[0]

class Command(BaseCommand):
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
        make_option('--only',
                    default=False,
                    dest="only",
                    action="store_true",
                    help="only print out the named parameters, don't include the defaults"), )
    help = ("Print out the configuration options in place on this computer")

    def handle(self, *args, **options):

        result = 0
        if options["only"]:
            display_params = []
        else:
            display_params = ["DEFAULT_FROM_EMAIL", "EMAIL_BACKEND",
                              "EMAIL_HOST", "EMAIL_SUBJECT_PREFIX",
                              "SESSION_COOKIE_SECURE", "DATABASES"]
        for arg in args:
            display_params.append(arg)

        for param in display_params:
            try:
                print "%s: %s" % (param,
                                  pprint.pformat(getattr(settings, param)))
            except AttributeError:
                print "%s: was not found in settings" % param
                result = 1

        return result
