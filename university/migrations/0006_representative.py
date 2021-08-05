# Generated by Django 3.2.5 on 2021-08-04 17:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0003_user_username'),
        ('university', '0005_courselink'),
    ]

    operations = [
        migrations.CreateModel(
            name='Representative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64, verbose_name='title')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='representatives', to='university.department')),
                ('tguser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='representative', to='telegrambot.user')),
            ],
            options={
                'verbose_name': 'Representative',
                'verbose_name_plural': 'Representatives',
            },
        ),
    ]
