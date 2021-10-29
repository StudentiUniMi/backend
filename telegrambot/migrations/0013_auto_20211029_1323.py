# Generated by Django 3.2.8 on 2021-10-29 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0012_telegramuserbot_session_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='id',
            field=models.BigIntegerField(help_text='Set the ID to 0 if you want an userbot to actually create the group', primary_key=True, serialize=False, unique=True, verbose_name='Telegram group ID'),
        ),
        migrations.AlterField(
            model_name='telegramuserbot',
            name='session_file',
            field=models.FileField(upload_to='userbot-sessions/', verbose_name='telethon session file'),
        ),
        migrations.CreateModel(
            name='BotWhitelist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=64, unique=True, verbose_name='username')),
                ('whitelisted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='telegrambot.user')),
            ],
            options={
                'verbose_name': "Whitelist'd bot",
                'verbose_name_plural': "Whitelist'd bots",
            },
        ),
    ]