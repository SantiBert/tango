# Generated by Django 4.2.11 on 2024-08-28 23:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investors', '0003_inversortemporal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inversortemporal',
            name='founding_year',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
