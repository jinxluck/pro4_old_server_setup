# Generated by Django 2.2.10 on 2020-03-02 16:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demo_module', '0002_auto_20200302_1620'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inbound_teststand_package',
            name='embedded_file',
        ),
        migrations.RemoveField(
            model_name='inbound_teststand_package',
            name='embedded_file_format',
        ),
    ]
