# Generated by Django 5.2 on 2025-05-16 03:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usrinfo', '0004_alter_postlikes_liked_users_alter_postlikes_post'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userlikes',
            name='liked_users',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_likes_users', to='usrinfo.profile'),
        ),
    ]
