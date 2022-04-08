# Generated by Django 3.2.9 on 2022-03-20 22:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0015_botwhitelist'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramLog',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('event', models.IntegerField(choices=[(0, 'CHAT_DOES_NOT_EXIST'), (5, 'MODERATION_INFO'), (1, 'MODERATION_WARN'), (2, 'MODERATION_KICK'), (3, 'MODERATION_BAN'), (4, 'MODERATION_MUTE'), (6, 'MODERATION_FREE'), (7, 'MODERATION_SUPERBAN'), (11, 'MODERATION_SUPERFREE'), (8, 'USER_JOINED'), (9, 'USER_LEFT'), (10, 'NOT_ENOUGH_RIGHTS'), (12, 'TELEGRAM_ERROR'), (13, 'USER_CALLED_ADMIN'), (14, 'MODERATION_DEL'), (15, 'WHITELIST_BOT'), (16, 'BROADCAST')])),
                ('reason', models.TextField(blank=True, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField()),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='telegrambot.group')),
                ('issuer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='log_as_issuer', to='telegrambot.user')),
                ('target', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='log_as_target', to='telegrambot.user')),
            ],
        ),
    ]