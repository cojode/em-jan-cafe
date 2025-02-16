import decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from typing import List, Dict


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
            # ! bad validation
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

    def update_dishes(self, new_dishes: List[Dict[str, int]]):
        """
        Updates the dishes in the order.

        Args:
            new_dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.

        Raises:
            ValidationError: If a dish ID is invalid or validation fails.
        """

        with transaction.atomic():
            self.dishes.clear()
            for dish_data in new_dishes:
                try:
                    dish_id = dish_data["dish_id"]
                    dish = Dish.objects.get(id=dish_id)
                except Dish.DoesNotExist as e:
                    raise ValidationError(
                        f"Dish validation failed: dish id [{dish_id}] does not exist"
                    ) from e
                except ValueError as e:
                    raise ValidationError(
                        "Dish validation failed: missing dish_id field"
                    ) from e
                OrderDish.objects.create(
                    order=self,
                    dish=dish,
                    quantity=dish_data.get("amount", 1),
                )
            self.total_price = self.calculate_total_price()
            self.save(update_fields=["total_price"])

    @classmethod
    def create_order(cls, table_number: int, dishes: List[Dict[str, int]]):
        """
        Creates a new order with the specified table number and dishes.

        Args:
            table_number (int): The table number for the order.
            dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.

        Returns:
            Order: The newly created order.

        Raises:
            ValidationError: If a dish ID is invalid or validation fails.
        """
        with transaction.atomic():
            order = cls(table_number=table_number)
            order.save()
            order.update_dishes(dishes)
        return order


class OrderDish(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_dishes"
    )
    dish = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name="dish_orders"
    )
    quantity = models.PositiveSmallIntegerField(default=1)
