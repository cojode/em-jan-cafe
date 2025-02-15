from rest_framework.test import APITestCase
from rest_framework import status
from orders.models import OrderStatus
from orders.services import OrderService
from django.urls import reverse


class OrderAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.valid_order_data = {
            "table_number": 5,
            "items": [{"name": "Пицца", "cost": "10.50", "amount": "2"}],
        }

        self.invalid_order_data = {
            "table_number": -1,
            "items": [],
        }

        self.order = OrderService.create(
            self.valid_order_data["table_number"],
            self.valid_order_data["items"],
        )

        self.order_detail_url = reverse("order-detail", args=[self.order.pk])
        self.order_list_url = reverse("order-list")
        self.order_status_url = reverse("order-status", args=[self.order.pk])
        self.order_items_url = reverse("order-items", args=[self.order.pk])

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
        self.assertEqual(
            response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def test_get_order_success(self):
        response = self.client.get(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["table_number"], self.order.table_number
        )

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
        new_items = [{"name": "Картошечка", "cost": 8.99, "amount": 1}]
        response = self.client.patch(
            self.order_items_url, {"items": new_items}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["items"],
            [{"name": "Картошечка", "cost": "8.99", "amount": "1"}],
        )

    def test_update_order_items_invalid_fails(self):
        response = self.client.patch(
            self.order_items_url, {"items": []}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def test_update_order_items_with_missing_fields_fails(self):
        new_items = [{"name": "Картошечка", "amount": 1}]
        response = self.client.patch(
            self.order_items_url, {"items": new_items}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def test_update_items_of_nonexistent_order_fails(self):
        url = reverse("order-items", args=[999])
        response = self.client.patch(
            url,
            {"items": [{"name": "Картошечка", "cost": 8.99, "amount": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
