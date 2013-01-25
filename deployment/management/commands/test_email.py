import os, sys, pprint

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
from django.core.mail import send_mail, mail_admins, mail_managers

PROJECT_NAME = settings.SETTINGS_MODULE.split('.')[0]

class Command(BaseCommand):
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
        make_option('--admins',
                    default=False,
                    dest="admins",
                    action="store_true",
                    help="Send a test email to the project admins"),
        make_option('--managers',
                    default=False,
                    dest="managers",
                    action="store_true",
                    help="Send a test email to the project managers"),
        make_option('--from',
                    default=settings.DEFAULT_FROM_EMAIL,
                    dest="from",
                    help="Send a test email to the project managers"),
        #make_option('--connection',
                    #default=settings.EMAIL_BACKEND,
                    #dest="connection",
                    #help="Which backend to send mail with, defaults to"
                    #" settings.EMAIL_BACKEND"),
    )
    help = ("Send a test email to the list of recipients from the specified"
            " address, or using the DEFAULT_FROM_EMAIL if not specified,"
            " from is ignored when sending to managers or admins")

    def handle(self, *args, **options):

        result = 0
        subject = "Deployment Test Message"
        message = "Deployment Test Message Body.  This was sent using" \
                  " django_deployment to test the email configuration of a" \
                  " deployed project."
        sent_msg = False

        if options["verbosity"] > "1":
            print "Using %s" % settings.EMAIL_BACKEND

        if options['admins']:
            mail_admins(subject, message, fail_silently=False)
            sent_msg = True
        if options['managers']:
            mail_managers(subject, message, fail_silently=False)
            sent_msg = True

        if args:
            send_mail(subject, message, options["from"], args,
                      fail_silently=False)
        elif not sent_msg:
            raise CommandError("No recipient addresses were specified on the"
                               " command line")

        return result

