# Generated by Django 3.2.9 on 2022-07-02 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0021_auto_20220622_2256'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='welcome_model_en',
            field=models.TextField(default='<b>{greetings}</b> nel gruppo {title}\n\nIscriviti al canale @studenti_unimi', help_text='Available format parameters: {greetings} and {title}', null=True, verbose_name='Welcome model'),
        ),
        migrations.AddField(
            model_name='group',
            name='welcome_model_it',
            field=models.TextField(default='<b>{greetings}</b> nel gruppo {title}\n\nIscriviti al canale @studenti_unimi', help_text='Available format parameters: {greetings} and {title}', null=True, verbose_name='Welcome model'),
        ),
        migrations.AlterField(
            model_name='group',
            name='language',
            field=models.CharField(blank=True, choices=[('en', 'English'), ('it', 'Italian')], default='it', max_length=3, null=True, verbose_name='preferred language'),
        ),
    ]