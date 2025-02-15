import decimal
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from orders.models import Dish, Order, OrderDish, OrderStatus


class OrderServiceError(Exception):
    """Base exception for errors in the OrderService."""

    def __init__(self, message, details=None):
        self.message = message
        self.details = details


class SearchError(OrderServiceError):
    """Raised when a search operation fails, such as when no matching order is found."""


class ConstraintError(OrderServiceError):
    """Raised when a validation or constraint fails, such as invalid data or dish IDs."""


class OrderService:
    """Service class for managing orders, including creation, modification, and retrieval."""

    @staticmethod
    def create(table_number: int, dishes: List[Dict[str, int]]) -> Order:
        """Creates a new order with the specified table number and dishes.

        Args:
            table_number (int): The table number for the order.
            dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.

        Returns:
            Order: The newly created order.

        Raises:
            ConstraintError: If a dish ID is invalid or validation fails.
        """
        try:
            with transaction.atomic():
                order = Order.objects.create(table_number=table_number)
                order.save()

                for dish_data in dishes:
                    dish = Dish.objects.get(id=dish_data["dish_id"])
                    OrderDish.objects.create(order=order, dish=dish)
                order.total_price = order.calculate_total_price()
                order.save()
            return order
        except (ValidationError, Dish.DoesNotExist) as e:
            raise ConstraintError(
                str(e), {"table_number": table_number, "dishes": dishes}
            ) from e

    @staticmethod
    def _get_and_verify_unique_existance(**fields) -> Order:
        """Retrieves a unique order based on the provided filters.

        Args:
            **fields: Filters to search for the order.

        Returns:
            Order: The unique order matching the filters.

        Raises:
            SearchError: If no order is found or multiple orders match the filters.
        """
        try:
            return Order.objects.get(**fields)
        except Order.DoesNotExist as e:
            raise SearchError(
                "No order found with the provided filters.", fields
            ) from e
        except Order.MultipleObjectsReturned as e:
            raise SearchError(
                "Multiple orders found with the provided filters.", fields
            ) from e

    @staticmethod
    def search_by_id(order_id: int) -> Order:
        """Retrieves an order by its unique ID.

        Args:
            order_id (int): The ID of the order to retrieve.

        Returns:
            Order: The order with the specified ID.

        Raises:
            SearchError: If no order is found with the provided ID.
        """
        return OrderService._get_and_verify_unique_existance(id=order_id)

    @staticmethod
    def search_by_filters(
        normalized: bool = False, **filters: Dict[str, Optional[any]]
    ) -> List[Order]:
        """Searches for orders based on the provided filters.

        Args:
            normalized (bool, optional): If True, excludes None-valued keys from filters. Defaults to False.
            **filters: Filters to apply when searching for orders.

        Returns:
            List[Order]: A list of orders matching the filters.
        """
        provided_filters = (
            {key: val for key, val in filters.items() if val} if normalized else filters
        )
        return Order.objects.filter(**provided_filters).order_by("id")

    @staticmethod
    def remove_by_id(order_id: int) -> int:
        """Deletes an order by its ID.

        Args:
            order_id (int): The ID of the order to delete.

        Returns:
            int: The number of orders deleted (>1 if successful, 0 otherwise).

        Raises:
            SearchError: If no order is found with the provided ID.
        """
        order = OrderService._get_and_verify_unique_existance(id=order_id)
        return order.delete()[0]

    @staticmethod
    def modify_status_by_id(order_id: int, new_status: str) -> Order:
        """Updates the status of an order.

        Args:
            order_id (int): The ID of the order to update.
            new_status (str): The new status to apply.

        Returns:
            Order: The updated order.

        Raises:
            SearchError: If no order is found with the provided ID.
            ConstraintError: If the new status is invalid.
        """
        order = OrderService._get_and_verify_unique_existance(id=order_id)

        try:
            order.status = new_status
            order.save(update_fields=["status"])
        except ValidationError as e:
            raise ConstraintError(str(e), {"status": new_status}) from e

        return order

    @staticmethod
    def modify_dishes_by_id(order_id: int, new_dishes: List[Dict[str, int]]) -> Order:
        """Updates the dishes in an order.

        Args:
            order_id (int): The ID of the order to update.
            new_dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.

        Returns:
            Order: The updated order.

        Raises:
            SearchError: If no order is found with the provided ID.
            ConstraintError: If a dish ID is invalid or validation fails.
        """
        order = OrderService._get_and_verify_unique_existance(id=order_id)

        try:
            with transaction.atomic():
                order.dishes.clear()
                for dish_data in new_dishes:
                    dish = Dish.objects.get(id=dish_data["dish_id"])
                    OrderDish.objects.create(
                        order=order,
                        dish=dish,
                        quantity=dish_data.get("amount", 1),
                    )

                order.total_price = order.calculate_total_price()
                order.save(update_fields=["total_price"])

        except (ValidationError, Dish.DoesNotExist) as e:
            raise ConstraintError(str(e), {"dishes": new_dishes}) from e

        return order

    @staticmethod
    def calculate_profit() -> decimal.Decimal:
        """Calculates the total profit from all paid orders.

        Returns:
            decimal.Decimal: The total profit from paid orders.
        """
        paid_status = OrderStatus.STATUS_PAID
        return (
            Order.objects.filter(status=paid_status).aggregate(
                total_profit=Sum("total_price")
            )["total_profit"]
        ) or decimal.Decimal(0)
