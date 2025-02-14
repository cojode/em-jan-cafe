from orders.models import Order
from django.db.models import Sum
import decimal

from typing import List, Dict


class OrderServiceError(Exception):
    """Common error for all order service errors"""

class OrderService:
    @staticmethod
    def create(table_number: int, items: List[Dict[str, float]]) -> Order:
        total_price = sum(item["cost"] * item["amount"] for item in items)
        jsonable_items = [
            {k: str(v) for k, v in item.items()} for item in items
        ]
        new_order = Order.objects.create(
            table_number=table_number,
            items=jsonable_items,
            total_price=total_price,
        )
        return new_order

    @staticmethod
    def show_all() -> List[Dict]:
        return Order.objects.all().values()

    @staticmethod
    def _get_and_verify_existance(**fields) -> Order:
        """Searches by custom set of fields.

        Handles DoesNotExist, MultipleObjectsReturned
        error with reraising OrderServiceError
        with message, which contains failed set of fields.
        """
        try:
            return Order.objects.get(**fields)
        except Order.DoesNotExist as e:
            raise OrderServiceError(
                f"There are no order to be found: {str(fields)}"
            ) from e
        except Order.MultipleObjectsReturned as e:
            raise OrderServiceError(
                f"Multiple objects found with fields: {str(fields)}"
            ) from e

    @staticmethod
    def search_by_id(order_id: int) -> Order:
        return OrderService._get_and_verify_existance(id=order_id)

    @staticmethod
    def search_by_table_number(order_table_number: int) -> List[Order]:
        return Order.objects.filter(table_number=order_table_number)

    @staticmethod
    def remove_by_id(order_id: int) -> int:
        order = OrderService._get_and_verify_existance(id=order_id)
        return order.delete()[0]

    @staticmethod
    def modify_status_by_id(order_id: int, new_status: str) -> Order:
        order = OrderService._get_and_verify_existance(id=order_id)
        order.status = new_status
        order.save(update_fields=["status"])
        return order

    @staticmethod
    def calculate_profit() -> decimal.Decimal:
        paid_status = Order.STATUS_PAID
        return (
            Order.objects.filter(status=paid_status).aggregate(
                total_profit=Sum("total_price")
            )["total_profit"]
        ) or decimal.Decimal(0)
