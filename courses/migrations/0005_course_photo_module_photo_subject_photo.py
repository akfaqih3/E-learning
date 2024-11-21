# Generated by Django 5.1.1 on 2024-10-07 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_course_students'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='photo',
            field=models.ImageField(blank=True, upload_to='courses/courses/photos/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='module',
            name='photo',
            field=models.ImageField(blank=True, upload_to='courses/courses/modules/photos/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='subject',
            name='photo',
            field=models.ImageField(blank=True, upload_to='courses/subjects/photos/%Y/%m/%d/'),
        ),
    ]