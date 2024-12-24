# Generated by Django 4.2.11 on 2024-09-18 05:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('startups', '0003_startupcategory_startupsubcategory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='startup',
            name='industry',
        ),
        migrations.AddField(
            model_name='startup',
            name='industry_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='industry', to='startups.startupsubcategory'),
        ),
    ]
