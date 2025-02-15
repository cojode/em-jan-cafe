import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from orders.models import Order, OrderStatus


@pytest.mark.django_db
def test_order_creation():
    order = Order(
        table_number=1,
        items=[{"name": "Пицца", "cost": "10.50", "amount": "2"}],
        status=OrderStatus.STATUS_PENDING,
    )
    order.save()

    assert order.id is not None
    assert order.total_price == Decimal("21.00")
    assert order.status == OrderStatus.STATUS_PENDING


@pytest.mark.django_db
def test_order_validation():
    order = Order(
        table_number=1,
        items=[],
        status=OrderStatus.STATUS_PENDING,
    )
    with pytest.raises(ValidationError) as excinfo:
        order.save()
    assert "Bad item: empty list of items are not allowed" in str(
        excinfo.value
    )
    order = Order(
        table_number=1,
        items=[{"cost": "10.50"}],
        status=OrderStatus.STATUS_PENDING,
    )
    with pytest.raises(ValidationError) as excinfo:
        order.save()
    assert "Bad item: missing " in str(excinfo.value)


@pytest.mark.django_db
def test_order_status_validation():
    order = Order(
        table_number=1,
        items=[{"name": "Пицца", "cost": "10.50", "amount": "2"}],
        status="invalid_status",
    )
    with pytest.raises(ValidationError) as excinfo:
        order.save()
    assert "Status not allowed" in str(excinfo.value)


@pytest.mark.django_db
def test_order_total_price_calculation():
    # Создаем заказ с несколькими items
    order = Order(
        table_number=1,
        items=[
            {"name": "Пицца", "cost": "10.50", "amount": "2"},
            {"name": "Пицца", "cost": "5.00", "amount": "3"},
        ],
        status=OrderStatus.STATUS_PENDING,
    )
    order.save()
    assert order.total_price == Decimal("36.00")


@pytest.mark.django_db
def test_order_items_normalization():
    order = Order(
        table_number=1,
        items=[
            {"name": "Пицца", "cost": 10.54, "amount": 2},
            {"name": "Пицца", "cost": 5.00, "amount": 3},
        ],
        status=OrderStatus.STATUS_PENDING,
    )
    order.save()
    assert order.items == [
        {"name": "Пицца", "cost": "10.54", "amount": "2"},
        {"name": "Пицца", "cost": "5.0", "amount": "3"},
    ]
