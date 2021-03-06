# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-13 12:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommandLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(max_length=64)),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('arguments', django_extensions.db.fields.json.JSONField(default=dict)),
                ('options', django_extensions.db.fields.json.JSONField(default=dict)),
            ],
            options={
                'ordering': ('-when',),
            },
        ),
        migrations.CreateModel(
            name='SettingsModule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='commandline',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deployment.SettingsModule'),
        ),
    ]
