# Generated by Django 3.2.5 on 2021-08-29 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('university', '0008_auto_20210829_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursedegree',
            name='semester',
            field=models.SmallIntegerField(default=0, verbose_name='semester'),
        ),
        migrations.AlterField(
            model_name='coursedegree',
            name='year',
            field=models.SmallIntegerField(default=0, verbose_name='year'),
        ),
    ]
