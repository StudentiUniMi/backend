# Generated by Django 3.2.6 on 2021-09-04 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0011_telegramuserbot'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuserbot',
            name='session_file',
            field=models.FileField(blank=True, null=True, upload_to='userbot-sessions/', verbose_name='telethon session file'),
        ),
    ]
