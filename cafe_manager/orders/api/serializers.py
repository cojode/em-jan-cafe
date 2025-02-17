from rest_framework import serializers

from orders.models import Dish, Order, OrderDish


class OrderDishSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source="dish.name", read_only=True)
    price = serializers.DecimalField(
        source="dish.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderDish
        fields = ["dish_id", "dish_name", "quantity", "price"]


class AddDishSerializer(serializers.Serializer):
    dish_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class ListQueryParamsSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1, required=False, default=None)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1)
    dishes = serializers.ListField(child=AddDishSerializer(), allow_empty=False)


class WrappedDishSerializer(serializers.Serializer):
    dishes = serializers.ListField(child=AddDishSerializer(), allow_empty=False)


class OrderSerializer(serializers.ModelSerializer):
    dishes = OrderDishSerializer(source="order_dishes", many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "table_number", "total_price", "dishes", "status"]


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
