# Generated by Django 5.1.6 on 2025-02-15 17:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_orders_order_status_valid"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dish",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                (
                    "price",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("amount", models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name="order",
            name="items",
        ),
        migrations.CreateModel(
            name="OrderDish",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveSmallIntegerField(default=1)),
                (
                    "dish",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dish_orders",
                        to="orders.dish",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_dishes",
                        to="orders.order",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="dishes",
            field=models.ManyToManyField(through="orders.OrderDish", to="orders.dish"),
        ),
    ]
