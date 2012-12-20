import random
from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase, Client
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.test.utils import override_settings

from models import Configuration, AccessAttempt
from signals import lockout_signal

# Only run tests if they have axes in middleware

def get_random_ip():
    not_valid = [10,127,169,172]

    first = random.randrange(1,256)
    while first in not_valid:
        first = random.randrange(1,256)

    ip = ".".join([str(first), str(random.randrange(1,256)),
                   str(random.randrange(1,256)), str(random.randrange(1,256))])
    return ip

# Basically a functional test
@override_settings(AXES_LOCKOUT_TEMPLATE='', AXES_LOCKOUT_URL='')
class AccessAttemptTest(TestCase):
    NOT_GONNA_BE_PASSWORD = "sfdlermmvnLsefrlg0c9gjjPxmvLlkdf2#"
    NOT_GONNA_BE_USERNAME = "whywouldyouohwhy"

    def setUp(self):
        for i in range(0, random.randrange(10, 50)):
            username = "person%s" % i
            email = "%s@example.org" % username
            u = User.objects.create_user(email=email, username=username)
            u.is_staff = True
            u.save()
        config = Configuration.get_or_create()
        config.max_login_attempts = 3
        config.save()
        from middleware import FailedLoginMiddleware
        FailedLoginMiddleware.ENABLE_AXES_MIDDLEWARE = True

    def tearDown(self):
        from middleware import FailedLoginMiddleware
        FailedLoginMiddleware.ENABLE_AXES_MIDDLEWARE = False

    def _gen_bad_password(self):
        return AccessAttemptTest.NOT_GONNA_BE_PASSWORD + str(random.random())

    def _random_username(self, correct_username=False):
        if not correct_username:
            return (AccessAttemptTest.NOT_GONNA_BE_USERNAME +
                    str(random.random()))[:30]
        else:
            return random.choice(User.objects.filter(is_staff=True))

    def _attempt_login(self, correct_username=False, user="", username="", use_random_ip=False):
        if use_random_ip:
            ip = get_random_ip()
        else:
            ip = '127.0.0.1'

        if username:
            username=username
        else:
            username=self._random_username(correct_username)

        response = self.client.post(
        '/admin/', {'username': username,
                    'password': self._gen_bad_password()}, **{'REMOTE_ADDR':ip}
         )
        return response

    def test_login_max_ip(self, correct_username=False):
        self.signal_received = 0
        def test_log_lockout_receipt(sender, **kwargs):
            self.assertFalse(kwargs['user_lockout'])
            self.assertEqual(type(kwargs['attempt']), AccessAttempt)
            self.signal_received += 1
        lockout_signal.connect(test_log_lockout_receipt,
                               sender=AccessAttempt, dispatch_uid="uid")

        for i in range(0, Configuration.get_or_create().max_login_attempts):
            response = self._attempt_login(correct_username=correct_username)
            self.assertNotContains(response, "Account locked")
            self.assertFalse(self.signal_received)
        # So, we shouldn't have gotten a lock-out yet.
        # But we should get one now
        response = self._attempt_login()
        self.assertContains(response, "Account locked")
        self.assertEqual(1, self.signal_received)

        # piggyback test for the axes_reset command with --nosignal option
        self.signal_received = 0
        content = StringIO()
        call_command("axes_reset", verbosity=1, send_signal=False, stdout=content)
        self.assertEqual(content.getvalue(), 'All (4) AccessAttempt records deleted.')
        self.assertEqual(0, self.signal_received)


    def test_login_max_user(self):
        username = self._random_username(correct_username=True).username
        user = User.objects.get(username=username)

        self.signal_received = 0
        def test_log_lockout_receipt(sender, **kwargs):
            self.assertTrue(kwargs['user_lockout'])
            self.assertEqual(type(kwargs['attempt']), AccessAttempt)
            self.signal_received += 1
        lockout_signal.connect(test_log_lockout_receipt,
                               sender=AccessAttempt, dispatch_uid="uid")

        for i in range(0, Configuration.get_or_create().max_login_attempts):
            response = self._attempt_login(username=username, use_random_ip=True)
            self.assertNotContains(response, "Account locked")
            self.assertFalse(self.signal_received)

        # So, we shouldn't have gotten a lock-out yet.
        # But we should get one now
        response = self._attempt_login(username=username, use_random_ip=True)
        self.assertContains(response, "Account locked")
        self.assertEqual(1, self.signal_received)

        # piggyback test for the axes_reset command with nosignal option and
        # verbosity turned off (no output)
        self.signal_received = 0
        content = StringIO()
        call_command("axes_reset", username=username, verbosity=0,
                     send_signal=False, stdout=content)
        self.assertEqual(content.getvalue(), '')
        self.assertEqual(0, self.signal_received)

    def test_login_max_with_more(self, correct_username=False):
        for i in range(0, Configuration.get_or_create().max_login_attempts):
            response = self._attempt_login(correct_username=correct_username)
            self.assertNotContains(response, "Account locked")
        # So, we shouldn't have gotten a lock-out yet.
        # But we should get one now
        for i in range(0, 100):
            # try to log in a bunch of times
            response = self._attempt_login()
            self.assertContains(response, "Account locked")

    def test_login_max_user_with_more(self):
        username = self._random_username(correct_username=True).username
        for i in range(0, Configuration.get_or_create().max_login_attempts):
            response = self._attempt_login(username=username, use_random_ip=True)
            self.assertNotContains(response, "Account locked")
        # So, we shouldn't have gotten a lock-out yet.
        # But we should get one now
        for i in range(0, random.randrange(1, 100)):
            # try to log in a bunch of times
            response = self._attempt_login(username=username, use_random_ip=True)
            self.assertContains(response, "Account locked")

    def test_with_real_username_max(self):
        self.test_login_max_ip(correct_username=True)

    def test_with_real_username_max_with_more(self):
        self.test_login_max_with_more(correct_username=True)
