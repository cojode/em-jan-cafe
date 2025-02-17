import decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import OrderStatus
from orders.services import OrderService


class OrderAPITestCase(APITestCase):
    fixtures = ["example_dishes.json"]

    def setUp(self):
        self.valid_order_data = {
            "table_number": 5,
            "dishes": [{"dish_id": 5, "quantity": 2}],
        }

        self.invalid_order_data = {
            "table_number": -1,
            "dishes": [],
        }

        self.order = OrderService.create(
            self.valid_order_data["table_number"],
            self.valid_order_data["dishes"],
        )

        self.order_detail_url = reverse("order-detail", args=[self.order.pk])
        self.order_list_url = reverse("order-list")
        self.order_status_url = reverse("order-status", args=[self.order.pk])
        self.order_items_url = reverse("order-dishes", args=[self.order.pk])

    def test_create_order_success(self):
        response = self.client.post(
            self.order_list_url, self.valid_order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_order_with_empty_items_fails(self):
        response = self.client.post(
            self.order_list_url, self.invalid_order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_order_success(self):
        response = self.client.get(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["table_number"], self.order.table_number)

    def test_get_nonexistent_order_fails(self):
        response = self.client.get(reverse("order-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_order_status_success(self):
        response = self.client.patch(
            self.order_status_url, {"status": "ready"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ready")

    def test_update_order_status_invalid_fails(self):
        response = self.client.patch(
            self.order_status_url, {"status": "invalid_status"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_order_success(self):
        response = self.client.delete(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_nonexistent_order_fails(self):
        response = self.client.delete(reverse("order-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revenue_calculation(self):
        self.order.status = OrderStatus.STATUS_PAID
        self.order.save()
        response = self.client.get(reverse("order-revenue"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["revenue"], self.order.total_price)

    def test_pagination(self):
        response = self.client.get(self.order_list_url + "?page=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)

    def test_update_order_items_success(self):
        new_dishes = [{"dish_id": 1, "quantity": 1}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["dishes"],
            [
                {
                    "dish_id": 1,
                    "dish_name": "Margherita Pizza",
                    "price": "9.99",
                    "quantity": 1,
                }
            ],
        )

    def test_update_order_items_invalid_fails(self):
        response = self.client.patch(
            self.order_items_url, {"dishes": []}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_update_order_items_with_missing_fields_fails(self):
        new_items = [{"dish_id": 2}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_items}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_update_items_of_nonexistent_order_fails(self):
        url = reverse("order-dishes", args=[999])
        response = self.client.patch(
            url,
            {"dishes": [{"dish_id": 123, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_order_items_with_invalid_dish_id_fails(self):
        new_dishes = [{"dish_id": 999, "quantity": 1}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Dish validation failed: dish id", response.data["message"])

    def test_update_order_items_with_negative_quantity_fails(self):
        new_dishes = [{"dish_id": 1, "quantity": -1}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("Data validation error", response.data["message"])

    def test_update_order_items_with_zero_quantity_fails(self):
        new_dishes = [{"dish_id": 1, "quantity": 0}]  # Zero quantity
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("Data validation error", response.data["message"])

    def test_update_order_items_with_missing_dish_id_fails(self):
        new_dishes = [{"quantity": 1}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("Data validation error", response.data["message"])

    def test_update_order_items_with_non_numeric_amount_fails(self):
        new_dishes = [{"dish_id": 1, "quantity": "two"}]
        response = self.client.patch(
            self.order_items_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_complex_order_workflow(self):
        """
        Test a complex order workflow:
        1. Create an order.
        2. Update the order's dishes.
        3. Update the order's status to "ready".
        4. Update the order's status to "paid".
        5. Verify the revenue calculation.
        6. Delete the order.
        """
        # * Step 1: Create an order
        create_response = self.client.post(
            self.order_list_url, self.valid_order_data, format="json"
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        order_id = create_response.data["id"]

        # * Step 2: Update the order's dishes
        update_dishes_url = reverse("order-dishes", args=[order_id])
        new_dishes = [{"dish_id": 1, "quantity": 3}]
        update_dishes_response = self.client.patch(
            update_dishes_url, {"dishes": new_dishes}, format="json"
        )
        self.assertEqual(update_dishes_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(update_dishes_response.data["dishes"]), 1)

        # * Step 3: Update the order's status to "ready"
        update_status_url = reverse("order-status", args=[order_id])
        update_status_response = self.client.patch(
            update_status_url,
            {"status": OrderStatus.STATUS_READY},
            format="json",
        )
        self.assertEqual(update_status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            update_status_response.data["status"], OrderStatus.STATUS_READY
        )

        # * Step 4: Update the order's status to "paid"
        update_status_response = self.client.patch(
            update_status_url,
            {"status": OrderStatus.STATUS_PAID},
            format="json",
        )
        self.assertEqual(update_status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_status_response.data["status"], OrderStatus.STATUS_PAID)

        # * Step 5: Verify the revenue calculation
        revenue_url = reverse("order-revenue")
        revenue_response = self.client.get(revenue_url)
        self.assertEqual(revenue_response.status_code, status.HTTP_200_OK)

        # * Fetch the order to get the updated total price
        order_detail_url = reverse("order-detail", args=[order_id])
        order_detail_response = self.client.get(order_detail_url)
        self.assertEqual(order_detail_response.status_code, status.HTTP_200_OK)
        expected_revenue = decimal.Decimal(order_detail_response.data["total_price"])
        # ? Decimal comparasion
        self.assertAlmostEqual(revenue_response.data["revenue"], expected_revenue)

        # * Step 6: Delete the order
        delete_response = self.client.delete(order_detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # * Verify the order is deleted
        get_deleted_order_response = self.client.get(order_detail_url)
        self.assertEqual(
            get_deleted_order_response.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_everything_goes_wrong_but_still_works_fine(self):
        """
        Test a complex scenario where multiple things go wrong, but the system handles them gracefully:
        1. Create an order with invalid data (should fail).
        2. Create an order with valid data (should succeed).
        3. Update the order with invalid dishes (should fail).
        4. Update the order with valid dishes (should succeed).
        5. Update the order status to an invalid status (should fail).
        6. Update the order status to a valid status (should succeed).
        7. Attempt to delete a non-existent order (should fail).
        8. Delete the order (should succeed).
        9. Verify the revenue calculation after deleting the order (should still work).
        """
        # * Step 1: Create an order with invalid data (should fail)
        invalid_create_response = self.client.post(
            self.order_list_url, self.invalid_order_data, format="json"
        )
        self.assertEqual(
            invalid_create_response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        # * Step 2: Create an order with valid data (should succeed)
        valid_create_response = self.client.post(
            self.order_list_url, self.valid_order_data, format="json"
        )
        self.assertEqual(valid_create_response.status_code, status.HTTP_201_CREATED)
        order_id = valid_create_response.data["id"]

        # * Step 3: Update the order with invalid dishes (should fail)
        update_dishes_url = reverse("order-dishes", args=[order_id])
        invalid_dishes = [{"dish_id": 999, "quantity": 1}]
        invalid_update_dishes_response = self.client.patch(
            update_dishes_url, {"dishes": invalid_dishes}, format="json"
        )
        self.assertEqual(
            invalid_update_dishes_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # * Step 4: Update the order with valid dishes (should succeed)
        valid_dishes = [{"dish_id": 1, "quantity": 2}]  # Valid dish ID
        valid_update_dishes_response = self.client.patch(
            update_dishes_url, {"dishes": valid_dishes}, format="json"
        )
        self.assertEqual(valid_update_dishes_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(valid_update_dishes_response.data["dishes"]), 1)

        # * Step 5: Update the order status to an invalid status (should fail)
        update_status_url = reverse("order-status", args=[order_id])
        invalid_status_response = self.client.patch(
            update_status_url, {"status": "invalid_status"}, format="json"
        )
        self.assertEqual(
            invalid_status_response.status_code, status.HTTP_400_BAD_REQUEST
        )

        # * Step 6: Update the order status to a valid status (should succeed)
        valid_status_response = self.client.patch(
            update_status_url,
            {"status": OrderStatus.STATUS_READY},
            format="json",
        )
        self.assertEqual(valid_status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(valid_status_response.data["status"], OrderStatus.STATUS_READY)

        # * Step 7: Attempt to delete a non-existent order (should fail)
        non_existent_order_url = reverse("order-detail", args=[999])
        delete_non_existent_response = self.client.delete(non_existent_order_url)
        self.assertEqual(
            delete_non_existent_response.status_code, status.HTTP_404_NOT_FOUND
        )

        # * Step 8: Delete the order (should succeed)
        order_detail_url = reverse("order-detail", args=[order_id])
        delete_response = self.client.delete(order_detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # * Step 9: Verify the revenue calculation after deleting the order (should still work)
        revenue_url = reverse("order-revenue")
        revenue_response = self.client.get(revenue_url)
        self.assertEqual(revenue_response.status_code, status.HTTP_200_OK)
        self.assertAlmostEqual(
            revenue_response.data["revenue"], decimal.Decimal("0.00")
        )
