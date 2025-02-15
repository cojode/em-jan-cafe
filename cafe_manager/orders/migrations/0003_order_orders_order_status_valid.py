# Generated by Django 5.1.6 on 2025-02-15 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_remove_order_created_at'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(condition=models.Q(('status__in', ['pending', 'ready', 'paid'])), name='orders_order_status_valid'),
        ),
    ]
