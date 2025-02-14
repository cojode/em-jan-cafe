from django.db import models
from typing import List, Dict
import decimal

# Create your models here.


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_READY = "ready"
    STATUS_PAID = "paid"

    STATUS_CHOICES = [
        (STATUS_PENDING, "В ожидании"),
        (STATUS_READY, "Готово"),
        (STATUS_PAID, "Оплачено"),
    ]

    table_number: int = models.IntegerField()
    items: List[Dict[str, str]] = models.JSONField()
    total_price: decimal.Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    status: str = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
