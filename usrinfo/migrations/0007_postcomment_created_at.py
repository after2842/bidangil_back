# Generated by Django 5.2 on 2025-05-20 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usrinfo', '0006_postcomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='postcomment',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
