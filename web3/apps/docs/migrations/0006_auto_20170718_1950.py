# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-18 19:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0005_auto_20170718_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='posted',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='posted',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]