# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-18 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0006_auto_20170718_1950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='edited',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='posted',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='edited',
            field=models.DateTimeField(blank=True, db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='posted',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
