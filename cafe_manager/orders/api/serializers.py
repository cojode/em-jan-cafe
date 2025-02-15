from rest_framework import serializers

from orders.models import Dish, Order


class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ["id", "name", "price"]


class AddDishSerializer(serializers.Serializer):
    dish_id = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=1)


class ListQueryParamsSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1, required=False, default=None)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1)
    dishes = serializers.ListField(child=AddDishSerializer(), allow_empty=False)


class WrappedDishSerializer(serializers.Serializer):
    dishes = serializers.ListField(child=AddDishSerializer(), allow_empty=False)


class OrderSerializer(serializers.ModelSerializer):
    dishes = DishSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "table_number", "total_price", "dishes", "status"]


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
