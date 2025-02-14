from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.services import OrderService, OrderServiceError
from .serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    UpdateStatusSerializer,
)


def handle_service_error(wrapper):
    from orders.utils import protective_call

    return protective_call(exception_error_response, OrderServiceError)(
        wrapper
    )


def exception_error_response(e: Exception):
    return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


def validation_error_response(serializer):
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(APIView):
    @handle_service_error
    def get(self, _):
        orders = OrderService.show_all()
        serialized_orders = [OrderSerializer(order).data for order in orders]
        return Response(
            {"count": len(serialized_orders), "items": serialized_orders}
        )


class OrderCreateView(APIView):
    @handle_service_error
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer)
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


class OrderTableNumberView(APIView):
    @handle_service_error
    def get(self, _, table_number):
        orders = OrderService.search_by_table_number(
            self.kwargs["table_number"]
        )
        serialized_orders = [OrderSerializer(order).data for order in orders]
        return Response(
            {"count": len(serialized_orders), "items": serialized_orders}
        )


class OrderIdStatusView(APIView):
    @handle_service_error
    def patch(self, request, order_id):
        serializer = UpdateStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer)

        print(serializer.validated_data)
        new_status = serializer.validated_data["status"]

        order = OrderService.modify_status_by_id(
            self.kwargs["order_id"], new_status
        )

        return Response(OrderSerializer(order).data)


class TotalProfitView(APIView):
    @handle_service_error
    def get(self, _):
        return Response({"total_profit": OrderService.calculate_profit()})
