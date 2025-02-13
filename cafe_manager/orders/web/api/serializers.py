from rest_framework import serializers
from orders.models import Order


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.0
    )
    amount = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1)
    items = serializers.ListField(child=ItemSerializer(), allow_empty=False)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "table_number", "total_price", "items", "status"]
