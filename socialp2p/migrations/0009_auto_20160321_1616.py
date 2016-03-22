# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-21 22:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socialp2p', '0008_auto_20160321_0024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='visibility',
            field=models.CharField(choices=[('PUBLIC', 'Public to All'), ('SERVERONLY', 'Public to Local'), ('FOAF', 'Friends of Friends'), ('FRIENDS', 'Friends'), ('LFS', 'Local Friends'), ('ONL', 'Only This Person ...'), ('PRIVATE', 'Only Me')], default='PRIVATE', max_length=3),
        ),
    ]