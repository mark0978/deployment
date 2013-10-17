import deployment, os

from django.test import TestCase, Client
from django.conf import settings
from django.test.utils import override_settings

from .templatetags import deployment_tags

class TemplateTagTestCase(TestCase):
    def test_flipslash(self):
        self.assertEqual("This/Is/Correct", deployment_tags.flipslash("This\\Is\Correct"))

    def test_module_path(self):
        self.assertEqual(os.path.dirname(deployment.__file__),
                         deployment_tags.module_path("deployment"))