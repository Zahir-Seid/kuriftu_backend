# Generated by Django 5.2 on 2025-04-12 05:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EngagementLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('referral_signup', 'Referral Signup'), ('completed_booking', 'Completed Booking'), ('combo_experience', 'Combo Experience'), ('birthday_claim', 'Birthday Claim'), ('lottery_play', 'Lottery Play'), ('family_booking', 'Family Booking')], max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
