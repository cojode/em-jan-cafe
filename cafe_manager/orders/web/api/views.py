from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.services.order_service import OrderService, OrderServiceError
from .serializers import CreateOrderSerializer, OrderSerializer

from orders.utils import protective_call


def exception_error_response(e: Exception):
    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def handle_service_error(wrapper):
    return protective_call(exception_error_response, OrderServiceError)(
        wrapper
    )


class OrderListView(APIView):
    @handle_service_error
    def get(self):
        orders = OrderService.show_all()
        return Response(orders)


class OrderCreateView(APIView):

    @handle_service_error
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        table_number = serializer.validated_data["table_number"]
        items = serializer.validated_data["items"]

        order = OrderService.create(table_number, items)
        return Response({"id": order.pk}, status=status.HTTP_201_CREATED)


class OrderIdView(APIView):
    @handle_service_error
    def get(self, _, order_id):
        order = OrderService.search_by_id(self.kwargs["order_id"])
        return Response(OrderSerializer(order).data)

    @handle_service_error
    def delete(self, _, order_id):
        deleted_amount = OrderService.remove_by_id(self.kwargs["order_id"])
        return Response(deleted_amount)
