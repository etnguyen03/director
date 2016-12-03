# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-03 00:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualMachine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True)),
                ('description', models.TextField(blank=True)),
                ('users', models.ManyToManyField(related_name='vm_groups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
