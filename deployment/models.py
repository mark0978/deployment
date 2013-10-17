from django.db import models
from django.utils import timezone
from django_extensions.db.fields.json import JSONField


class SettingsModule(models.Model):
    name = models.CharField(max_length=128)

class CommandLine(models.Model):
    command = models.CharField(max_length=64)
    module = models.ForeignKey(SettingsModule)
    when = models.DateTimeField(default=timezone.now())
    arguments = JSONField()
    options = JSONField()

    class Meta:
        ordering = ('-when', )