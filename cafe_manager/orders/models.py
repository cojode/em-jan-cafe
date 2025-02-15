from django.db import models
from typing import List, Dict
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import decimal


# Create your models here.
class OrderStatus(models.TextChoices):
    STATUS_PENDING = "pending", _("В ожидании")
    STATUS_READY = "ready", _("Готово")
    STATUS_PAID = "paid", _("Оплачено")

    @staticmethod
    def verify_status(status: str):
        if not status in [choice[0] for choice in OrderStatus.choices]:
            raise ValidationError("Status not allowed: ")


class Order(models.Model):
    table_number: int = models.IntegerField()
    items: List[Dict[str, str]] = models.JSONField()
    total_price: decimal.Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    status: str = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.STATUS_PENDING,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[choice[0] for choice in OrderStatus.choices]
                ),
                name="%(app_label)s_%(class)s_status_valid",
            )
        ]

    def create(self, *args, **kwargs):
        OrderStatus.verify_status(self.status)
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        OrderStatus.verify_status(self.status)
        super().save(*args, **kwargs)
