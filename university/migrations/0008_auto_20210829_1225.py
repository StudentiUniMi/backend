# Generated by Django 3.2.5 on 2021-08-29 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0010_userprivilege_can_superban_members'),
        ('university', '0007_auto_20210827_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='degree',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='degree', to='telegrambot.group'),
        ),
        migrations.AddField(
            model_name='degree',
            name='icon',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='icon'),
        ),
        migrations.AddField(
            model_name='department',
            name='icon',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='icon'),
        ),
        migrations.AddField(
            model_name='department',
            name='slug',
            field=models.CharField(default='default_slug', max_length=64, unique=True, verbose_name='slug'),
        ),
    ]