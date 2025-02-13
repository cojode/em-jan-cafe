from django.db import models

# Create your models here.


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "В ожидании"),
        ("ready", "Готово"),
        ("paid", "Оплачено"),
    ]

    table_number = models.IntegerField()
    items = models.JSONField()
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
