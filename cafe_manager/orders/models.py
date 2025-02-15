import decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Dish(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)


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
    dishes = models.ManyToManyField(Dish, through="OrderDish")
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
        total = decimal.Decimal(0)
        for order_dish in self.order_dishes.all():
            total += order_dish.dish.price * order_dish.quantity
        return total

    def save(self, *args, **kwargs):
        """Saves an order."""
        self.validate_table_number()
        OrderStatus.verify_status(self.status)
        super().save(*args, **kwargs)


class OrderDish(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_dishes"
    )
    dish = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name="dish_orders"
    )
    quantity = models.PositiveSmallIntegerField(default=1)
