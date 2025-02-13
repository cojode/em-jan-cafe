from orders.models import Order

class OrderService:

    @staticmethod
    def create(table_number: int, items: list) -> Order:
        total_price = sum(item["cost"] for item in items)
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
        return Order.objects.all()

    @staticmethod
    def remove(): ...

    @staticmethod
    def search(): ...

    @staticmethod
    def modify_status(): ...

    @staticmethod
    def calculate_profit(): ...
