from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.services import OrderService, OrderServiceError
from .serializers import (
    CreateOrderSerializer,
    ListQueryParamsSerializer,
    OrderSerializer,
    UpdateStatusSerializer,
)
from orders.utils import protective_call


def not_found_error_response(e: OrderServiceError):
    return Response(
        {"message": e.message, "details": e.details},
        status=status.HTTP_404_NOT_FOUND,
    )


def validation_error_response(serializer):
    return Response(
        {"message": "Data validation error.", "details": serializer.errors},
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def handle_not_found_error(wrapper):
    return protective_call(not_found_error_response, OrderServiceError)(
        wrapper
    )


class OrderListView(APIView):

    def get(self, request: Request):
        serializer = ListQueryParamsSerializer(data=request.query_params)
        if not serializer.is_valid():
            return validation_error_response(serializer)
        orders = OrderService.search_by_filters(**serializer.validated_data)
        serialized_orders = [OrderSerializer(order).data for order in orders]
        return Response(
            {"count": len(serialized_orders), "items": serialized_orders}
        )


class OrderCreateView(APIView):

    @handle_not_found_error
    def post(self, request: Request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer)
        table_number = serializer.validated_data["table_number"]
        items = serializer.validated_data["items"]

        order = OrderService.create(table_number, items)
        return Response({"id": order.pk}, status=status.HTTP_201_CREATED)


class OrderIdView(APIView):

    @handle_not_found_error
    def get(self, _, order_id: int):
        order = OrderService.search_by_id(self.kwargs["order_id"])
        return Response(OrderSerializer(order).data)

    @handle_not_found_error
    def delete(self, _, order_id: int):
        deleted_amount = OrderService.remove_by_id(self.kwargs["order_id"])
        return Response(deleted_amount)


class OrderIdStatusView(APIView):

    @handle_not_found_error
    def patch(self, request, order_id: int):
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
    def get(self, _):
        return Response({"total_profit": OrderService.calculate_profit()})
