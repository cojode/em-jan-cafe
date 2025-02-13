from orders.models import Order


class OrderServiceError(Exception):
    """Common error for all order service errors"""


class OrderService:
    @staticmethod
    def create(table_number: int, items: list) -> Order:
        total_price = sum(item["cost"] * item["amount"] for item in items)
        jsonable_items = [
            {k: str(v) for k, v in item.items()} for item in items
        ]
        new_order = Order.objects.create(
            table_number=table_number,
            items=jsonable_items,
            total_price=total_price,
            # ? by default: status="pending",
        )
        return new_order

    @staticmethod
    def show_all():
        return Order.objects.all().values()

    @staticmethod
    def _verify_existance_and_find_by_id(order_id: int) -> Order:
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist as e:
            raise OrderServiceError(
                f"There are no order with id [{order_id}] to be found"
            ) from e

    @staticmethod
    def search_by_id(order_id: int) -> Order:
        return OrderService._verify_existance_and_find_by_id(order_id)

    @staticmethod
    def remove_by_id(order_id: int) -> int:
        order = OrderService._verify_existance_and_find_by_id(order_id)
        return order.delete()[0]

    @staticmethod
    def search_by_table_number(): ...

    @staticmethod
    def modify_status(): ...

    @staticmethod
    def calculate_profit(): ...
