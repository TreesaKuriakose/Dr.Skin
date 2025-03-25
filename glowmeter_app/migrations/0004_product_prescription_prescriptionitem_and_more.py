# Generated by Django 5.1.7 on 2025-03-25 05:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glowmeter_app', '0003_user_profile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('usage_instructions', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to='glowmeter_app.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrescriptionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=100)),
                ('duration', models.CharField(max_length=100)),
                ('prescription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='glowmeter_app.prescription')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='glowmeter_app.product')),
            ],
        ),
        migrations.AddField(
            model_name='prescription',
            name='products',
            field=models.ManyToManyField(through='glowmeter_app.PrescriptionItem', to='glowmeter_app.product'),
        ),
    ]
