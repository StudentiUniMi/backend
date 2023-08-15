# Generated by Django 3.2.9 on 2023-08-15 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('telegrambot', '0026_auto_20230815_1642'), ('telegrambot', '0027_auto_20230815_1659')]

    dependencies = [
        ('telegrambot', '0025_alter_telegrambot_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='extra_group_category',
            field=models.CharField(blank=True, choices=[('u', 'University group'), ('a', 'Announcement group'), ('s', 'Student association group')], max_length=2, null=True, verbose_name='Extra group category'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_description',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group description'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_description_en',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group description'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_description_it',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group description'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_name',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group name'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_name_en',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group name'),
        ),
        migrations.AddField(
            model_name='group',
            name='extra_group_name_it',
            field=models.TextField(blank=True, max_length=150, null=True, verbose_name='Extra group name'),
        ),
    ]
