# Generated by Django 3.2.9 on 2022-03-31 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0016_telegramlog'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userprivilege',
            options={'verbose_name': 'User privilege (deprecated)', 'verbose_name_plural': 'User privileges (deprecated)'},
        ),
    ]
