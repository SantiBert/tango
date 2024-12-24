# Generated by Django 4.2.11 on 2024-08-27 05:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('investors', '0001_initial'),
        ('startups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentround',
            name='startup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='startups.startup'),
        ),
    ]
