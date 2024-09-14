# Generated by Django 3.2.9 on 2023-10-22 13:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0027_auto_20231022_1324'),
        ('university', '0013_featuredgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='featuredgroup',
            name='order',
            field=models.PositiveIntegerField(default=100, verbose_name='Order'),
        ),
        migrations.AlterField(
            model_name='featuredgroup',
            name='category',
            field=models.CharField(choices=[('u', 'University group'), ('a', 'Announcement group'), ('s', 'Student association group')], max_length=2, verbose_name='Extra group category'),
        ),
        migrations.AlterField(
            model_name='featuredgroup',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='telegrambot.group'),
        ),
    ]