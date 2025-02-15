from orders.models import Order, OrderStatus
from django.db.models import Sum
from django.core.exceptions import ValidationError
import decimal

from typing import List, Dict, Optional


class OrderServiceError(Exception):
    """Common error for all order service errors"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details


class SearchError(OrderServiceError):
    """Occurs on any failed search attempts."""


class ConstraintError(OrderServiceError):
    """Occurs on any validation failures."""


class OrderService:

    @staticmethod
    def create(table_number: int, items: List[Dict[str, float]]) -> Order:
        """Creates new order entry.

        :param table_number: table_number field
        :type table_number: int
        :param items: items in order, represented as JSONField in a model
        :type items: List[Dict[str, float]]
        :raises ConstraintError: one of the field failed constraint
        :return: newly created Order
        :rtype: Order
        """
        try:
            return Order.objects.create(
                table_number=table_number,
                items=items,
            )
        except ValidationError as e:
            raise ConstraintError(
                str(e), {"table_number": table_number, "items": items}
            ) from e

    @staticmethod
    def _get_and_verify_unique_existance(**fields) -> Order:
        """Searches by custom set of fields with **model.objects.get()** method.

        Raises **OrderServiceError** if order with given fields
        is not unique or does not exists.

        Handles **DoesNotExist**, **MultipleObjectsReturned**
        error with reraising **OrderServiceError**
        with message, which contains failed set of fields.

        :raises SearchError: on model.DoesNotExist
        :raises SearchError: on model.MultipleObjectsReturned
        :return: found unique order entry
        :rtype: Order
        """
        try:
            return Order.objects.get(**fields)
        except Order.DoesNotExist as e:
            raise SearchError("There are no order to be found.", fields) from e
        except Order.MultipleObjectsReturned as e:
            raise SearchError(
                "Multiple objects found with fields.", fields
            ) from e

    @staticmethod
    def search_by_id(order_id: int) -> Order:
        """Implements direct access to an order through its id.

        :param order_id: order id
        :type order_id: int
        :return: found order
        :raises SearchError: failed to found an order with provided id
        :rtype: Order
        """
        return OrderService._get_and_verify_unique_existance(id=order_id)

    @staticmethod
    def search_by_filters(
        normalized: bool = False, **filters: Dict[str, Optional[any]]
    ) -> List[Order]:
        """Search for a multiple order objects by provided filters.

        Uses model.objects.filter(); if a key in a filter is a None value,
        by default it would be considered. Provide **normalized=True** to
        not consider None values and discard them from filters.

        Does not raises **OrderServiceError** if no order to be found,
        returns empty list instead.

        :param normalized: discard None-valued keys from filters, defaults to False
        :type normalized: bool, optional
        :return: _description_
        :rtype: List[Order]
        """
        provided_filters = (
            {key: val for key, val in filters.items() if val}
            if normalized
            else filters
        )
        return Order.objects.filter(**provided_filters)

    @staticmethod
    def remove_by_id(order_id: int) -> int:
        """Implements deletion an order through its id.

        :param order_id: order id
        :type order_id: int
        :return: found order
        :raises SearchError: failed to found an order with provided id
        :rtype: Order
        """
        order = OrderService._get_and_verify_unique_existance(id=order_id)
        return order.delete()[0]

    @staticmethod
    def _modify_order_with_fields_by_id(order_id: int, **fields) -> Order:
        """Updates an order with custom dict of fields and values

        :param order_id: order id to be updated
        :type order_id: int
        :raises SearchError: failed to found an order with provided id
        :raises ConstraintError: not allowed field or field value
        :return: updated order
        :rtype: Order
        """
        order = OrderService._get_and_verify_unique_existance(id=order_id)
        for field, new_value in fields.items():
            setattr(order, field, new_value)
        try:
            order.save(update_fields=fields.keys())
        except ValidationError as e:
            raise ConstraintError(str(e), fields) from e
        return order

    @staticmethod
    def modify_status_by_id(order_id: int, new_status: str) -> Order:
        """Updates an order with provided status.

        :param order_id: order id to be updated
        :type order_id: int
        :param new_status: status to be applied
        :type new_status: str
        :return: updated order
        :raises SearchError: failed to found an order with provided id
        :raises ConstraintError: not allowed status
        :rtype: Order
        """
        return OrderService._modify_order_with_fields_by_id(
            order_id=order_id, status=new_status
        )

    @staticmethod
    def modify_items_by_id(order_id: int, new_items: List[Dict[str, float]]):
        """Updates an order with provided items.

        :param order_id: order id to be updated
        :type order_id: int
        :param new_status: items to be applied
        :type new_status: str
        :return: updated order
        :raises SearchError: failed to found an order with provided id
        :raises ConstraintError: not allowed items
        :rtype: Order
        """
        return OrderService._modify_order_with_fields_by_id(
            order_id=order_id, items=new_items
        )

    @staticmethod
    def calculate_profit() -> decimal.Decimal:
        """Calculates total profit on existing orders.

        Sums total_price fields from orders with OrderStatus.STATUS_PAID status

        :return: current order revenue
        :rtype: decimal.Decimal
        """
        paid_status = OrderStatus.STATUS_PAID
        return (
            Order.objects.filter(status=paid_status).aggregate(
                total_profit=Sum("total_price")
            )["total_profit"]
        ) or decimal.Decimal(0)
