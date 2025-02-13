from rest_framework import serializers


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.0
    )
    amount = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1)
    items = serializers.ListField(child=ItemSerializer(), allow_empty=False)
