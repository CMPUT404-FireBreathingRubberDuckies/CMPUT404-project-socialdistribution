# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-21 06:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socialp2p', '0007_auto_20160321_0023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='access_password',
            field=models.CharField(max_length=100),
        ),
    ]
