# Generated by Django 4.2.11 on 2024-08-29 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investors', '0004_alter_inversortemporal_founding_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='inversortemporal',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
