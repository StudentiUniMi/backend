# Generated by Django 3.2.5 on 2021-07-25 15:50

import datetime
from django.db import migrations, models
import django.db.models.deletion
import telegram.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False, unique=True, verbose_name='Telegram group ID')),
                ('title', models.CharField(max_length=512, verbose_name='title')),
                ('description', models.TextField(blank=True, max_length=2048, null=True, verbose_name='description')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to=telegram.models.Group._format_filename)),
                ('invite_link', models.CharField(blank=True, max_length=128, null=True, verbose_name='invite link')),
            ],
            options={
                'verbose_name': 'Telegram group',
                'verbose_name_plural': 'Telegram groups',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='GroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Telegram group membership',
                'verbose_name_plural': 'Telegram groups memberships',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.PositiveBigIntegerField(primary_key=True, serialize=False, unique=True, verbose_name='Telegram user ID')),
                ('first_name', models.CharField(max_length=256, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=256, null=True, verbose_name='last name')),
                ('reputation', models.IntegerField(default=0, verbose_name='reputation')),
                ('warn_count', models.IntegerField(default=0, verbose_name='warn count')),
                ('banned', models.BooleanField(default=False, verbose_name='banned?')),
                ('permissions_level', models.IntegerField(default=0, verbose_name='permission level')),
                ('last_seen', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'verbose_name': 'Telegram user',
                'verbose_name_plural': 'Telegram users',
                'ordering': ['id'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['id'], name='id_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['id', 'banned'], name='banned_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['first_name', 'last_name'], name='name_idx'),
        ),
        migrations.AddField(
            model_name='groupmembership',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram.group'),
        ),
        migrations.AddField(
            model_name='groupmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram.user'),
        ),
        migrations.AddField(
            model_name='group',
            name='members',
            field=models.ManyToManyField(related_name='member_of', through='telegram.GroupMembership', to='telegram.User'),
        ),
        migrations.AddField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups_owned', to='telegram.user'),
        ),
    ]
