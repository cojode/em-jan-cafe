from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.services.order_service import OrderService
from .serializers import CreateOrderSerializer


class OrderCreateView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        table_number = serializer.validated_data["table_number"]
        items = serializer.validated_data["items"]
        try:
            order = OrderService.create(table_number, items)
            return Response({"id": order.pk}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
