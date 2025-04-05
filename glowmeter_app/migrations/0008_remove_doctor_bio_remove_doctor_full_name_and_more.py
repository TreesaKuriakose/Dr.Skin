# Generated by Django 5.0.2 on 2025-04-05 05:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glowmeter_app', '0007_doctoravailability'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='bio',
        ),
        migrations.RemoveField(
            model_name='doctor',
            name='full_name',
        ),
        migrations.RemoveField(
            model_name='doctor',
            name='profile_picture',
        ),
        migrations.RemoveField(
            model_name='doctor',
            name='specialty',
        ),
        migrations.AddField(
            model_name='doctor',
            name='consultation_fee',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='doctor',
            name='experience_years',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='doctor',
            name='gpay_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='doctor',
            name='qualification',
            field=models.CharField(default='MBBS', max_length=200),
        ),
        migrations.AddField(
            model_name='doctor',
            name='specialization',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100)),
                ('gpay_transaction_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('consultation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='glowmeter_app.consultation')),
            ],
        ),
    ]
