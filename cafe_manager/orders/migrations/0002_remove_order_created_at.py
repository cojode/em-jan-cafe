# Generated by Django 5.1.6 on 2025-02-13 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="created_at",
        ),
    ]
