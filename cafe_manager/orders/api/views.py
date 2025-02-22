import logging
from functools import wraps
from typing import Callable

from django.core.paginator import Paginator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.services import (ConstraintError, OrderService, OrderServiceError,
                             SearchError)

from .serializers import (CreateOrderSerializer, ListQueryParamsSerializer,
                          OrderSerializer, StatusSerializer,
                          WrappedDishSerializer)
from .swagger_schemas import (BAD_REQUEST_RESPONSE, NOT_FOUND_RESPONSE,
                              ORDER_CREATE_RESPONSE, ORDER_DELETE_RESPONSE,
                              ORDER_DETAIL_RESPONSE, ORDER_LIST_RESPONSE,
                              ORDER_STATUS_UPDATE_RESPONSE, REVENUE_RESPONSE,
                              VALIDATION_ERROR_RESPONSE)

logger = logging.getLogger(__name__)


def protective_call(
    error_handler: Callable[[Exception], any], *errors_to_except: Exception
):
    """
    A decorator factory to handle specific exceptions and return a custom error response.

    Args:
        error_handler (Callable[[Exception], any]): A function to handle the exception.
        *errors_to_except (Exception): Variable list of exceptions to catch.

    Returns:
        Callable: A decorator that wraps the function and handles specified exceptions.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors_to_except as e:
                logger.debug("Error handled from %s: %s", func.__name__, str(e))
                return error_handler(e)

        return wrapper

    return decorator


def handle_service_search_error(wrapper):
    """
    Decorator to handle SearchError exceptions and return a 404 response.

    Args:
        wrapper: The function to wrap.

    Returns:
        Callable: A decorated function that handles SearchError.
    """
    return protective_call(not_found_error_response, SearchError)(wrapper)


def handle_service_constraint_error(wrapper):
    """
    Decorator to handle ConstraintError exceptions and return a 400 response.

    Args:
        wrapper: The function to wrap.

    Returns:
        Callable: A decorated function that handles ConstraintError.
    """
    return protective_call(bad_request_error_response, ConstraintError)(wrapper)


def not_found_error_response(e: OrderServiceError) -> Response:
    """
    Returns a 404 Not Found response with error details.

    Args:
        e (OrderServiceError): The exception containing error details.

    Returns:
        Response: A DRF Response object with a 404 status code.
    """
    return Response(
        {"message": e.message, "details": e.details},
        status=status.HTTP_404_NOT_FOUND,
    )


def bad_request_error_response(e: OrderServiceError) -> Response:
    """
    Returns a 400 Bad Request response with error details.

    Args:
        e (OrderServiceError): The exception containing error details.

    Returns:
        Response: A DRF Response object with a 400 status code.
    """
    return Response(
        {"message": e.message, "details": e.details},
        status=status.HTTP_400_BAD_REQUEST,
    )


def validation_error_response(serializer) -> Response:
    """
    Returns a 422 Unprocessable Entity response with validation error details.

    Args:
        serializer: The serializer containing validation errors.

    Returns:
        Response: A DRF Response object with a 422 status code.
    """
    return Response(
        {"message": "Data validation error.", "details": serializer.errors},
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


class OrderView(APIView):

    @swagger_auto_schema(
        operation_description="Retrieve a paginated list of orders.",
        manual_parameters=[
            openapi.Parameter(
                "pagesize",
                openapi.IN_QUERY,
                description="Number of orders per page",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "table_number",
                openapi.IN_QUERY,
                description="Filter by table number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Filter by order status",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "id",
                openapi.IN_QUERY,
                description="Filter by order ID",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: ORDER_LIST_RESPONSE,
            422: VALIDATION_ERROR_RESPONSE,
        },
    )
    def get(self, request: Request) -> Response:
        """
        Retrieve a paginated list of orders based on query parameters.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: A DRF Response object containing the paginated list of orders.
        """
        serializer = ListQueryParamsSerializer(data=request.query_params)
        if not serializer.is_valid():
            logger.debug("Validation error in OrderView GET: %s", serializer.errors)
            return validation_error_response(serializer)

        orders = OrderService.search_by_filters(
            **serializer.validated_data, normalized=True
        )

        page_size = request.query_params.get("pagesize", 10)
        page_number = request.query_params.get("page", 1)

        paginator = Paginator(orders, page_size)

        page = paginator.get_page(page_number)

        serialized_orders = OrderSerializer(page, many=True).data

        logger.info(
            "Retrieved %d orders from page %d",
            len(serialized_orders),
            page_number,
        )
        return Response(
            {"count": paginator.count, "items": serialized_orders},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="Create a new order.",
        request_body=CreateOrderSerializer,
        responses={
            201: ORDER_CREATE_RESPONSE,
            400: BAD_REQUEST_RESPONSE,
            422: VALIDATION_ERROR_RESPONSE,
        },
    )
    @handle_service_constraint_error
    def post(self, request: Request) -> Response:
        """
        Create a new order.

        Args:
            request (Request): The HTTP request object containing order data.

        Returns:
            Response: A DRF Response object with the created order's details.
        """
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            logger.debug("Validation error in OrderView POST: %s", serializer.errors)
            return validation_error_response(serializer)

        table_number = serializer.validated_data["table_number"]
        dishes = serializer.validated_data["dishes"]

        order = OrderService.create(table_number, dishes)
        logger.info("Created order with ID %d", order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderIdView(APIView):

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific order.",
        responses={
            200: ORDER_DETAIL_RESPONSE,
            404: NOT_FOUND_RESPONSE,
        },
    )
    @handle_service_search_error
    def get(self, _, order_id: int) -> Response:
        """
        Retrieve details of a specific order by its ID.

        Args:
            _: Unused request object.
            order_id (int): The ID of the order to retrieve.

        Returns:
            Response: A DRF Response object containing the order details.
        """
        order = OrderService.search_by_id(order_id)
        logger.info("Retrieved order with ID %d", order_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete an order.",
        responses={204: ORDER_DELETE_RESPONSE, 404: NOT_FOUND_RESPONSE},
    )
    @handle_service_search_error
    def delete(self, _, order_id: int) -> Response:
        """
        Delete a specific order by its ID.

        Args:
            _: Unused request object.
            order_id (int): The ID of the order to delete.

        Returns:
            Response: A DRF Response object with a 204 No Content status.
        """
        OrderService.remove_by_id(order_id)
        logger.info("Deleted order with ID %d", order_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderIdStatusView(APIView):

    @swagger_auto_schema(
        operation_description="Update the status of an order.",
        request_body=StatusSerializer,
        responses={
            200: openapi.Response("Order updated", OrderSerializer),
            400: BAD_REQUEST_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            422: VALIDATION_ERROR_RESPONSE,
        },
    )
    @handle_service_search_error
    @handle_service_constraint_error
    def patch(self, request: Request, order_id: int) -> Response:
        """
        Update the status of a specific order by its ID.

        Args:
            request (Request): The HTTP request object containing the new status.
            order_id (int): The ID of the order to update.

        Returns:
            Response: A DRF Response object containing the updated order details.
        """
        serializer = StatusSerializer(data=request.data)
        if not serializer.is_valid():
            logger.debug(
                "Validation error in OrderIdStatusView PATCH: %s",
                serializer.errors,
            )
            return validation_error_response(serializer)

        new_status = serializer.validated_data["status"]
        order = OrderService.modify_status_by_id(order_id, new_status)

        logger.info("Updated status of order %d to %s", order_id, new_status)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderIdDishesView(APIView):

    @swagger_auto_schema(
        operation_description="Update the dishes of an order.",
        request_body=WrappedDishSerializer,
        responses={
            200: openapi.Response("Order updated", OrderSerializer),
            400: BAD_REQUEST_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            422: VALIDATION_ERROR_RESPONSE,
        },
    )
    @handle_service_search_error
    @handle_service_constraint_error
    def patch(self, request: Request, order_id: int) -> Response:
        """
        Update the dishes of a specific order by its ID.

        Args:
            request (Request): The HTTP request object containing the new dishes.
            order_id (int): The ID of the order to update.

        Returns:
            Response: A DRF Response object containing the updated order details.
        """
        serializer = WrappedDishSerializer(data=request.data)
        if not serializer.is_valid():
            logger.debug(
                "Validation error in OrderIdDishesView PATCH: %s",
                serializer.errors,
            )
            return validation_error_response(serializer)

        new_dishes = serializer.validated_data["dishes"]
        order = OrderService.modify_dishes_by_id(order_id, new_dishes)

        logger.info("Updated dishes of order %d", order_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class RevenueView(APIView):

    @swagger_auto_schema(
        operation_description="Retrieve the total revenue.",
        responses={200: REVENUE_RESPONSE},
    )
    def get(self, _) -> Response:
        """
        Retrieve the total revenue.

        Args:
            _: Unused request object.

        Returns:
            Response: A DRF Response object containing the revenue.
        """
        revenue = OrderService.calculate_profit()
        logger.info("Retrieved revenue: %f", revenue)
        return Response(
            {"revenue": revenue},
            status=status.HTTP_200_OK,
        )
