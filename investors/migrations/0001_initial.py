# Generated by Django 4.2.11 on 2024-08-27 05:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InvestmentRound',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_type', models.CharField(max_length=150)),
                ('amount', models.IntegerField(blank=True, null=True)),
                ('raised_amount', models.IntegerField(blank=True, null=True)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvestorUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firm_name', models.CharField(max_length=150)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('amount_invested', models.IntegerField()),
                ('invested_type', models.CharField(max_length=1000)),
                ('is_verificated', models.CharField(choices=[('verified', 'Verified'), ('not_verified', 'Not Verified'), ('pending', 'Pending')], default='pending', max_length=150)),
                ('is_active', models.BooleanField(default=True)),
                ('round', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='investors', to='investors.investmentround')),
            ],
        ),
    ]