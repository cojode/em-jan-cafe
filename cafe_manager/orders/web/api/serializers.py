from rest_framework import serializers
from orders.models import Order


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.0,
    )
    amount = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(min_value=1)
    items = serializers.ListField(child=ItemSerializer(), allow_empty=False)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "table_number", "total_price", "items", "status"]


class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.CharField()

    def validate_status(self, value):
        """
        Validate that the status is one of the allowed choices.
        """
        allowed_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Allowed statuses are: {allowed_statuses}"
            )
        return value
