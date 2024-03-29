# Generated by Django 3.2.9 on 2022-09-11 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('university', '0011_alter_representative_degree_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Professor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=64, verbose_name='first name')),
                ('last_name', models.CharField(max_length=64, verbose_name='last name')),
                ('url', models.URLField(blank=True, max_length=256, null=True, verbose_name='url')),
            ],
            options={
                'verbose_name': 'Professor',
                'verbose_name_plural': 'Professors',
                'unique_together': {('first_name', 'last_name')},
            },
        ),
        migrations.AddField(
            model_name='course',
            name='professor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='university.professor'),
        ),
    ]
