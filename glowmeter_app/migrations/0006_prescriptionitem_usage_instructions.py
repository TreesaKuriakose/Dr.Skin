# Generated by Django 5.0.2 on 2025-03-29 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glowmeter_app', '0005_product_created_at_product_image_product_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescriptionitem',
            name='usage_instructions',
            field=models.TextField(blank=True),
        ),
    ]
