# Generated by Django 3.2.5 on 2021-07-25 15:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('telegrambot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('cfu', models.PositiveSmallIntegerField(verbose_name='CFUs')),
                ('wiki_link', models.CharField(blank=True, max_length=128, null=True, verbose_name='wiki link')),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
            ],
        ),
        migrations.CreateModel(
            name='Degree',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('type', models.CharField(choices=[('B', 'Triennale'), ('M', 'Magistrale'), ('C', 'Laurea a ciclo unico')], max_length=1, verbose_name='degree type')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='degrees', to='university.department')),
            ],
            options={
                'verbose_name': 'Degree',
                'verbose_name_plural': 'Degrees',
            },
        ),
        migrations.CreateModel(
            name='CourseDegree',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField(default=0, verbose_name='year')),
                ('semester', models.PositiveSmallIntegerField(default=0, verbose_name='semester')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='university.course')),
                ('degree', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='university.degree')),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='degree',
            field=models.ManyToManyField(through='university.CourseDegree', to='university.Degree'),
        ),
        migrations.AddField(
            model_name='course',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='telegrambot.group'),
        ),
    ]
