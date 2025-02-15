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
            raise ValidationError("Status not allowed:")


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

    def validate_items(self):
        """Checks whether items is not empty or (cost, amount) is present"""
        if not self.items:
            raise ValidationError(
                "Bad item: empty list of items are not allowed"
            )

        for item in self.items:
            needed_fields = ["name", "cost", "amount"]
            missing_fields = [
                verify_field
                for verify_field in needed_fields
                if verify_field not in item
            ]
            if missing_fields:
                raise ValidationError(f"Bad item: missing {missing_fields}")

    def validate_table_number(self):
        """Checks whether table_number is assignable as a positive integer."""
        try:
            assert int(self.table_number) > 0
        except (ValueError, AssertionError) as e:
            raise ValidationError(
                "Bad table_number: should be a positive integer"
            ) from e

    def calculate_total_price(self):
        """Calculate total price."""
        return sum(
            decimal.Decimal(item["cost"]) * int(item["amount"])
            for item in self.items
        )

    def normalize_items(self):
        """Convert item values to string to make it jsonable."""
        self.items = [
            {k: str(v) for k, v in item.items()} for item in self.items
        ]

    def save(self, *args, **kwargs):
        """Saves an order."""
        self.validate_table_number()
        self.validate_items()
        self.total_price = self.calculate_total_price()
        self.normalize_items()
        OrderStatus.verify_status(self.status)
        super().save(*args, **kwargs)
