import pytest
from decimal import Decimal
from orders.models import Order, OrderStatus
from orders.services import (
    OrderService,
    OrderServiceError,
    ConstraintError,
    SearchError,
)


@pytest.mark.django_db
def test_create_order():
    table_number = 5
    items = [
        {"name": "Пицца", "cost": 500.0, "amount": 2},
        {"name": "Салат", "cost": 300.0, "amount": 1},
    ]

    order = OrderService.create(table_number=table_number, items=items)

    assert order.table_number == table_number
    assert order.items == [
        {"name": "Пицца", "cost": "500.0", "amount": "2"},
        {"name": "Салат", "cost": "300.0", "amount": "1"},
    ]
    assert order.total_price == Decimal("1300.0")


@pytest.mark.django_db
def test_search_by_id():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    found_order = OrderService.search_by_id(order.id)

    assert found_order.id == order.id
    assert found_order.table_number == order.table_number


@pytest.mark.django_db
def test_search_by_id_not_found():
    with pytest.raises(SearchError) as exc_info:
        OrderService.search_by_id(999)

    assert "There are no order to be found." in str(exc_info.value)


@pytest.mark.django_db
def test_search_by_filters():
    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PAID,
    )
    Order.objects.create(
        table_number=2,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "1"}],
    )

    orders = OrderService.search_by_filters(status=OrderStatus.STATUS_PAID)

    assert len(orders) == 1
    assert orders[0].table_number == 1


@pytest.mark.django_db
def test_remove_by_id():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    delete_count = OrderService.remove_by_id(order.id)

    assert delete_count == 1
    assert Order.objects.filter(id=order.id).count() == 0


@pytest.mark.django_db
def test_remove_by_id_not_found():
    with pytest.raises(SearchError) as exc_info:
        OrderService.remove_by_id(999)

    assert "There are no order to be found." in str(exc_info.value)


@pytest.mark.django_db
def test_modify_status_by_id():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )

    updated_order = OrderService.modify_status_by_id(
        order.id, OrderStatus.STATUS_READY
    )

    assert updated_order.status == OrderStatus.STATUS_READY


@pytest.mark.django_db
def test_modify_status_by_id_not_found():
    with pytest.raises(SearchError) as exc_info:
        OrderService.modify_status_by_id(999, OrderStatus.STATUS_READY)

    assert "There are no order to be found." in str(exc_info.value)


@pytest.mark.django_db
def test_calculate_profit_specified_total_price():
    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PAID,
    )
    Order.objects.create(
        table_number=2,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PAID,
    )
    Order.objects.create(
        table_number=3,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )

    profit = OrderService.calculate_profit()

    assert profit == Decimal("2000.0")


@pytest.mark.django_db
def test_calculate_profit_no_paid_orders():
    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        total_price=Decimal("1000.0"),
        status=OrderStatus.STATUS_PENDING,
    )

    profit = OrderService.calculate_profit()

    assert profit == Decimal("0.0")


@pytest.mark.django_db
def test_get_and_verify_unique_existance():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    found_order = OrderService._get_and_verify_unique_existance(id=order.id)
    assert found_order.id == order.id

    with pytest.raises(OrderServiceError) as exc_info:
        OrderService._get_and_verify_unique_existance(id=999)
    assert "There are no order to be found." in str(exc_info.value)

    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )
    with pytest.raises(OrderServiceError) as exc_info:
        OrderService._get_and_verify_unique_existance(table_number=1)
    assert "Multiple objects found with fields." in str(exc_info.value)


@pytest.mark.django_db
def test_search_by_filters_normalized():
    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )
    Order.objects.create(
        table_number=2,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_READY,
    )

    orders = OrderService.search_by_filters(
        normalized=True, status=None, table_number=1
    )
    assert len(orders) == 1
    assert orders[0].table_number == 1

    orders = OrderService.search_by_filters(
        normalized=True, status=None, table_number=None
    )
    assert len(orders) == 2


@pytest.mark.django_db
def test_remove_by_id_multiple():
    order1 = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )
    order2 = Order.objects.create(
        table_number=2,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    delete_count = OrderService.remove_by_id(order1.id)
    assert delete_count == 1
    assert Order.objects.filter(id=order1.id).count() == 0
    assert Order.objects.filter(id=order2.id).count() == 1


@pytest.mark.django_db
def test_modify_status_by_id_invalid_status():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )

    with pytest.raises(OrderServiceError):
        OrderService.modify_status_by_id(order.id, "bad status")


@pytest.mark.django_db
def test_calculate_profit_no_orders():
    profit = OrderService.calculate_profit()
    assert profit == Decimal("0.0")


@pytest.mark.django_db
def test_calculate_profit_mixed_statuses():
    Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
        status=OrderStatus.STATUS_PAID,
    )
    Order.objects.create(
        table_number=2,
        items=[{"name": "Пицца", "cost": "200.0", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )
    Order.objects.create(
        table_number=3,
        items=[{"name": "Пицца", "cost": "1000.0", "amount": "2"}],
        status=OrderStatus.STATUS_PAID,
    )

    profit = OrderService.calculate_profit()
    assert profit == Decimal("3000.0")


@pytest.mark.django_db
def test_create_bad_items_order():
    with pytest.raises(ConstraintError):
        OrderService.create(table_number=3, items=[{"bar": "foo"}])

    with pytest.raises(ConstraintError):
        OrderService.create(table_number=3, items=[])

    with pytest.raises(ConstraintError):
        OrderService.create(
            table_number=3,
            items=[
                {"name": "Пицца", "cost": "1000.0", "amount": "2"},
                {"bar": "foo"},
            ],
        )

    with pytest.raises(ConstraintError):
        OrderService.create(
            table_number=3,
            items=[
                {"name": "Пицца", "cost": "1000.0", "amount": "2"},
                {"name": "Пицца", "amount": "2"},
            ],
        )

    with pytest.raises(ConstraintError):
        OrderService.create(
            table_number=3,
            items=[
                {"name": "Пицца", "cost": "1000.0", "amount": "2"},
                {"name": "Пицца", "cost": "200"},
            ],
        )


@pytest.mark.django_db
def test_modify_items_by_id():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    updated_order = OrderService.modify_items_by_id(
        order.id, [{"name": "Пицца", "cost": "500.0", "amount": "4"}]
    )

    assert updated_order.items == [
        {"name": "Пицца", "cost": "500.0", "amount": "4"}
    ]


@pytest.mark.django_db
def test_modify_items_by_id_not_found():
    with pytest.raises(SearchError) as exc_info:
        OrderService.modify_items_by_id(999, OrderStatus.STATUS_READY)

    assert "There are no order to be found." in str(exc_info.value)


@pytest.mark.django_db
def test_modify_items_by_id_bad_items():
    order = Order.objects.create(
        table_number=1,
        items=[{"name": "Пицца", "cost": "500.0", "amount": "2"}],
    )

    with pytest.raises(ConstraintError):
        OrderService.modify_items_by_id(
            order.id,
            [
                {"name": "Пицца", "cost": "1000.0", "amount": "2"},
                {"name": "Пицца", "cost": "200"},
            ],
        )

    assert order.items == [{"name": "Пицца", "cost": "500.0", "amount": "2"}]
