from drf_yasg import openapi

from .serializers import OrderSerializer

error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
        "data": openapi.Schema(type=openapi.TYPE_OBJECT, default=None, example=None),
        "error": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "message": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Error message"
                ),
                "details": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Detailed error information (field-specific errors or constraints)",
                ),
            },
        ),
    },
    example={
        "success": False,
        "data": None,
        "error": {
            "message": "Data validation error.",
            "details": {"field_name": ["This field is required."]},
        },
    },
)

BAD_REQUEST_RESPONSE = openapi.Response("Bad Request", error_schema)
VALIDATION_ERROR_RESPONSE = openapi.Response("Validation Error", error_schema)

NOT_FOUND_RESPONSE = openapi.Response(
    "Not Found",
    openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
            "data": openapi.Schema(
                type=openapi.TYPE_OBJECT, default=None, example=None
            ),
            "error": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, description="Error message"
                    ),
                    "details": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Additional details",
                    ),
                },
            ),
        },
        example={
            "success": False,
            "data": None,
            "error": {
                "message": "Order not found.",
                "details": "No order found with the provided ID.",
            },
        },
    ),
)


def success_response_schema(data_schema):
    """
    Generates a Swagger schema for success responses.

    Args:
        data_schema (openapi.Schema): The actual data structure returned in a successful response.

    Returns:
        openapi.Schema: A success response schema.
    """
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
            "data": data_schema,
            "error": openapi.Schema(
                type=openapi.TYPE_OBJECT, default=None, example=None
            ),
        },
        example={
            "success": True,
            "data": getattr(data_schema, "example", {}),
            "error": None,
        },
    )


ORDER_LIST_RESPONSE = openapi.Response(
    "Successful order list retrieval",
    success_response_schema(
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                    ),
                ),
            },
            example={
                "count": 3,
                "items": [
                    {
                        "id": 1,
                        "table_number": 5,
                        "total_price": "45.50",
                        "status": "pending",
                        "dishes": ["..."],
                    },
                    {
                        "id": 2,
                        "table_number": 7,
                        "total_price": "30.00",
                        "status": "completed",
                        "dishes": ["..."],
                    },
                    {
                        "id": 3,
                        "table_number": 2,
                        "total_price": "55.20",
                        "status": "in_progress",
                        "dishes": ["..."],
                    },
                ],
            },
        )
    ),
)

ORDER_DETAIL_RESPONSE = openapi.Response(
    "Successful order retrieval",
    success_response_schema(OrderSerializer().data),
)

ORDER_CREATE_RESPONSE = openapi.Response(
    "Order created successfully",
    success_response_schema(OrderSerializer().data),
)

ORDER_DELETE_RESPONSE = openapi.Response(
    "Order deleted successfully",
    success_response_schema(openapi.Schema(type=openapi.TYPE_OBJECT, default=None)),
)

ORDER_STATUS_UPDATE_RESPONSE = openapi.Response(
    "Order status updated successfully",
    success_response_schema(OrderSerializer().data),
)

REVENUE_RESPONSE = openapi.Response(
    "Revenue retrieved successfully",
    success_response_schema(
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "revenue": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format=openapi.FORMAT_FLOAT,
                    example=250.75,
                ),
            },
            example={"revenue": 250.75},
        )
    ),
)
