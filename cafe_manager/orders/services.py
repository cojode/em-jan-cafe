import decimal
from typing import Dict, List, Optional


from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Prefetch

from orders.models import Dish, Order, OrderStatus, OrderDish


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
    def _custom_prefetch() -> Prefetch:
        """Stores a DishOrder Prefetch to be applied for inner methods.

        :return: Obtain custom setuped Prefetch for
        :rtype: Prefetch
        """
        return Prefetch(
            "order_dishes",
            queryset=OrderDish.objects.select_related("dish").annotate(
                dish_name=F("dish__name"),
                price=F("dish__price"),
            ),
            to_attr="prefetched_dishes",
        )

    @staticmethod
    def _get_and_verify_unique_existance(
        apply_prefetch: bool = False, **fields
    ) -> Order:
        """Retrieves a unique order based on the provided filters.

        Args:
            apply_prefetch: (bool, optional): If True, applies OrderDish prefetch for a direct access to a Dish'es. Defaults to False.
            **fields: Filters to search for the order.

        Returns:
            Order: The unique order matching the filters.

        Raises:
            SearchError: If no order is found or multiple orders match the filters.
        """
        try:
            tuned_objects = (
                Order.objects.prefetch_related(OrderService._custom_prefetch())
                if apply_prefetch
                else Order.objects
            )
            return tuned_objects.get(**fields)
        except Order.DoesNotExist as e:
            raise SearchError(
                "No order found with the provided filters.", fields
            ) from e
        except Order.MultipleObjectsReturned as e:
            raise SearchError(
                "Multiple orders found with the provided filters.", fields
            ) from e

    @staticmethod
    def create(table_number: int, dishes: List[Dict[str, int]]) -> Order:
        """
        Creates a new order with the specified table number and dishes.

        Args:
            table_number (int): The table number for the order.
            dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.

        Returns:
            Order: The newly created order.

        Raises:
            ConstraintError: If a dish ID is invalid or validation fails.
        """
        try:
            return Order.create_order(table_number, dishes)
        except ValidationError as e:
            raise ConstraintError(
                str(e), {"table_number": table_number, "dishes": dishes}
            ) from e

    @staticmethod
    def search_by_id(order_id: int, apply_prefetch: bool = False) -> Order:
        """Retrieves an order by its unique ID.

        Args:
            order_id (int): The ID of the order to retrieve.
            apply_prefetch: (bool, optional): If True, applies OrderDish prefetch for a direct access to a Dish'es. Defaults to False.

        Returns:
            Order: The order with the specified ID.

        Raises:
            SearchError: If no order is found with the provided ID.
        """
        return OrderService._get_and_verify_unique_existance(
            apply_prefetch=apply_prefetch, id=order_id
        )

    @staticmethod
    def search_by_filters(
        apply_prefetch: bool = False,
        normalized: bool = False,
        **filters: Dict[str, Optional[any]]
    ) -> List[Order]:
        """Searches for orders based on the provided filters.

        Args:
            apply_prefetch: (bool, optional): If True, applies OrderDish prefetch for a direct access to a Dish'es. Defaults to False.
            normalized (bool, optional): If True, excludes None-valued keys from filters. Defaults to False.
            **filters: Filters to apply when searching for orders.

        Returns:
            List[Order]: A list of orders matching the filters.
        """
        provided_filters = (
            {key: val for key, val in filters.items() if val} if normalized else filters
        )
        ordered_filtered_objects = Order.objects.filter(
            **provided_filters
        ).order_by("id")

        return (
            ordered_filtered_objects.prefetch_related(
                OrderService._custom_prefetch()
            )
            if apply_prefetch
            else ordered_filtered_objects
        )

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
    def modify_status_by_id(
        order_id: int, new_status: str, apply_prefetch: bool = False
    ) -> Order:
        """Updates the status of an order.

        Args:
            order_id (int): The ID of the order to update.
            new_status (str): The new status to apply.
            apply_prefetch: (bool, optional): If True, applies OrderDish prefetch for a direct access to a Dish'es. Defaults to False.

        Returns:
            Order: The updated order.

        Raises:
            SearchError: If no order is found with the provided ID.
            ConstraintError: If the new status is invalid.
        """
        order = OrderService._get_and_verify_unique_existance(
            apply_prefetch=apply_prefetch, id=order_id
        )

        try:
            order.status = new_status
            order.save(update_fields=["status"])
        except ValidationError as e:
            raise ConstraintError(str(e), {"status": new_status}) from e

        return order

    @staticmethod
    def modify_dishes_by_id(
        order_id: int,
        new_dishes_with_quantities: List[Dict[str, int]],
        apply_prefetch: bool = False,
    ) -> Order:
        """
        Updates the dishes in an order.

        Args:
            order_id (int): The ID of the order to update.
            new_dishes (List[Dict[str, int]]): A list of dictionaries containing dish IDs and quantities.
            apply_prefetch: (bool, optional): If True, applies OrderDish prefetch for a direct access to a Dish'es. Defaults to False.

        Returns:
            Order: The updated order.

        Raises:
            SearchError: If no order is found with the provided ID.
            ConstraintError: If a dish ID is invalid or validation fails.
        """
        order = OrderService._get_and_verify_unique_existance(
            apply_prefetch=apply_prefetch, id=order_id
        )
        try:
            order.update_dishes(new_dishes_with_quantities)
        except ValidationError as e:
            raise ConstraintError(
                str(e), {"dishes_with_quantities": new_dishes_with_quantities}
            ) from e
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


class DishService:
    """Service class for dishes"""

    @staticmethod
    def all_dishes() -> List[Dish]:
        """Get all dishes presented"""
        return Dish.objects.all()
