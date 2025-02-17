from decimal import Decimal

from django.test import TestCase

from orders.models import Dish, Order, OrderDish, OrderStatus
from orders.services import (ConstraintError, OrderService, OrderServiceError,
                             SearchError)


class OrderServiceTests(TestCase):
    fixtures = ["example_dishes.json"]

    def test_create_order_success(self):
        """Test creating an order successfully."""
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)

        dishes = [{"dish_id": dish1.id}, {"dish_id": dish2.id}]
        order = OrderService.create(table_number=1, dishes=dishes)

        self.assertEqual(order.table_number, 1)
        self.assertEqual(order.status, OrderStatus.STATUS_PENDING)
        self.assertEqual(order.total_price, Decimal("21.98"))
        self.assertEqual(order.order_dishes.count(), 2)

    def test_create_order_invalid_dish(self):
        """Test creating an order with an invalid dish ID."""
        with self.assertRaises(ConstraintError) as context:
            OrderService.create(table_number=1, dishes=[{"dish_id": 999}])

        self.assertIn("Dish validation failed: dish id", str(context.exception))

    def test_search_by_id_success(self):
        """Test searching for an order by ID successfully."""
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)
        found_order = OrderService.search_by_id(order.id)

        self.assertEqual(found_order.id, order.id)
        self.assertEqual(found_order.table_number, 1)

    def test_search_by_id_not_found(self):
        """Test searching for an order by ID that does not exist."""
        with self.assertRaises(SearchError) as context:
            OrderService.search_by_id(999)

        self.assertIn(
            "No order found with the provided filters.", str(context.exception)
        )

    def test_search_by_filters_success(self):
        """Test searching for orders using filters."""
        Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)
        Order.objects.create(table_number=2, status=OrderStatus.STATUS_READY)

        orders = OrderService.search_by_filters(table_number=1)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].table_number, 1)

        orders = OrderService.search_by_filters(status=OrderStatus.STATUS_READY)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].status, OrderStatus.STATUS_READY)

    def test_search_by_filters_normalized(self):
        """Test searching for orders with normalized filters."""
        Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)

        orders = OrderService.search_by_filters(
            table_number=1, status=None, normalized=True
        )
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].table_number, 1)

    def test_remove_by_id_success(self):
        """Test removing an order by ID successfully."""
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)
        deleted_count = OrderService.remove_by_id(order.id)

        self.assertEqual(deleted_count, 1)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_remove_by_id_not_found(self):
        """Test removing an order by ID that does not exist."""
        with self.assertRaises(SearchError) as context:
            OrderService.remove_by_id(999)

        self.assertIn(
            "No order found with the provided filters.", str(context.exception)
        )

    def test_modify_status_by_id_success(self):
        """Test modifying an order's status successfully."""
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)
        updated_order = OrderService.modify_status_by_id(
            order.id, OrderStatus.STATUS_READY
        )

        self.assertEqual(updated_order.status, OrderStatus.STATUS_READY)

    def test_modify_status_by_id_invalid_status(self):
        """Test modifying an order's status with an invalid status."""
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)

        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_status_by_id(order.id, "invalid_status")

        self.assertIn("Status not allowed", str(context.exception))

    def test_modify_dishes_by_id_success(self):
        """Test modifying an order's dishes successfully."""
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)

        updated_order = OrderService.modify_dishes_by_id(
            order.id,
            [{"dish_id": dish1.id, "quantity": 2}, {"dish_id": dish2.id}],
        )

        self.assertEqual(
            updated_order.total_price,
            Decimal("31.97"),
        )
        self.assertEqual(updated_order.order_dishes.count(), 2)

    def test_modify_dishes_by_id_invalid_dish(self):
        """Test modifying an order's dishes with an invalid dish ID."""
        order = Order.objects.create(table_number=1, status=OrderStatus.STATUS_PENDING)

        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_dishes_by_id(order.id, [{"dish_id": 999}])

        self.assertIn("Dish validation failed: dish id", str(context.exception))

    def test_calculate_profit_success(self):
        """Test calculating total profit from paid orders."""
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)

        order1 = Order.objects.create(
            table_number=1,
            status=OrderStatus.STATUS_PAID,
            total_price=Decimal("10.99"),
        )
        OrderDish.objects.create(order=order1, dish=dish1, quantity=1)

        order2 = Order.objects.create(
            table_number=2,
            status=OrderStatus.STATUS_PAID,
            total_price=Decimal("17.98"),
        )
        OrderDish.objects.create(order=order2, dish=dish1, quantity=1)
        OrderDish.objects.create(order=order2, dish=dish2, quantity=1)

        profit = OrderService.calculate_profit()
        self.assertEqual(profit, Decimal("28.97"))

    def test_calculate_profit_no_paid_orders(self):
        """Test calculating profit when there are no paid orders."""
        profit = OrderService.calculate_profit()
        self.assertEqual(profit, Decimal("0"))

    def test_transaction_rollback_on_invalid_dish_update(self):
        """
        Test that the service layer rolls back transactions when an invalid dish update is attempted:
        1. Create an order with valid dishes.
        2. Attempt to update the order with invalid dishes (should fail).
        3. Verify that the original dishes remain unchanged.
        """
        # * Step 1: Create an order with valid dishes
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)
        order = OrderService.create(
            table_number=1,
            dishes=[{"dish_id": dish1.id}, {"dish_id": dish2.id}],
        )
        self.assertEqual(order.order_dishes.count(), 2)

        # * Step 2: Attempt to update the order with invalid dishes (should fail)
        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_dishes_by_id(order.id, [{"dish_id": 999}])
        self.assertIn("Dish validation failed: dish id", str(context.exception))

        # * Step 3: Verify that the original dishes remain unchanged
        order.refresh_from_db()
        self.assertEqual(order.order_dishes.count(), 2)
        self.assertEqual(order.total_price, Decimal("21.98"))

    def test_messing_up_transaction_based_logic(self):
        """
        Test transaction-based logic by simulating errors during order creation and updates:
        1. Attempt to create an order with invalid dishes (should fail and roll back).
        2. Create an order with valid dishes (should succeed).
        3. Attempt to update the order with invalid dishes (should fail and roll back).
        4. Verify that the order remains unchanged after failed updates.
        """
        # * Step 1: Attempt to create an order with invalid dishes (should fail and roll back)
        with self.assertRaises(ConstraintError) as context:
            OrderService.create(table_number=1, dishes=[{"dish_id": 999}])
        self.assertIn("Dish validation failed: dish id", str(context.exception))

        # * Verify that no order was created
        self.assertEqual(Order.objects.count(), 0)

        # * Step 2: Create an order with valid dishes (should succeed)
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)
        order = OrderService.create(
            table_number=1,
            dishes=[{"dish_id": dish1.id}, {"dish_id": dish2.id}],
        )
        self.assertEqual(order.order_dishes.count(), 2)

        # * Step 3: Attempt to update the order with invalid dishes (should fail and roll back)
        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_dishes_by_id(order.id, [{"dish_id": 999}])
        self.assertIn("Dish validation failed: dish id", str(context.exception))

        # * Step 4: Verify that the order remains unchanged after failed updates
        order.refresh_from_db()
        self.assertEqual(order.order_dishes.count(), 2)
        self.assertEqual(order.total_price, Decimal("21.98"))

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
        with self.assertRaises(ConstraintError) as context:
            OrderService.create(table_number=-1, dishes=[])
        self.assertIn("Bad table_number", str(context.exception))

        # * Step 2: Create an order with valid data (should succeed)
        dish1 = Dish.objects.get(id=1)
        dish2 = Dish.objects.get(id=2)
        order = OrderService.create(
            table_number=1,
            dishes=[{"dish_id": dish1.id}, {"dish_id": dish2.id}],
        )
        self.assertEqual(order.table_number, 1)
        self.assertEqual(order.status, OrderStatus.STATUS_PENDING)
        self.assertEqual(order.total_price, Decimal("21.98"))

        # * Step 3: Update the order with invalid dishes (should fail)
        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_dishes_by_id(order.id, [{"dish_id": 999}])
        self.assertIn("Dish validation failed: dish id", str(context.exception))

        # * Step 4: Update the order with valid dishes (should succeed)
        updated_order = OrderService.modify_dishes_by_id(
            order.id,
            [{"dish_id": dish1.id, "quantity": 2}, {"dish_id": dish2.id}],
        )
        self.assertEqual(updated_order.total_price, Decimal("31.97"))
        self.assertEqual(updated_order.order_dishes.count(), 2)

        # * Step 5: Update the order status to an invalid status (should fail)
        with self.assertRaises(ConstraintError) as context:
            OrderService.modify_status_by_id(order.id, "invalid_status")
        self.assertIn("Status not allowed", str(context.exception))

        # * Step 6: Update the order status to a valid status (should succeed)
        updated_order = OrderService.modify_status_by_id(
            order.id, OrderStatus.STATUS_READY
        )
        self.assertEqual(updated_order.status, OrderStatus.STATUS_READY)

        # * Step 7: Attempt to delete a non-existent order (should fail)
        with self.assertRaises(SearchError) as context:
            OrderService.remove_by_id(999)
        self.assertIn(
            "No order found with the provided filters.", str(context.exception)
        )

        # * Step 8: Delete the order (should succeed)
        deleted_count = OrderService.remove_by_id(order.id)
        # ? Three objects actually to be deleted - one for the order itself,
        # ? two for OrderDish relations
        self.assertEqual(deleted_count, 3)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

        # * Step 9: Verify the revenue calculation after deleting the order (should still work)
        profit = OrderService.calculate_profit()
        self.assertEqual(profit, Decimal("0"))

    def test_complex_order_workflow(self):
        """
        Test a complex order workflow in the service layer:
        1. Create an order with valid dishes.
        2. Update the order's dishes.
        3. Update the order's status to "ready".
        4. Update the order's status to "paid".
        5. Verify the revenue calculation.
        6. Delete the order.
        7. Verify the revenue calculation after deletion.
        """
        # * Step 1: Create an order with valid dishes
        dish1 = Dish.objects.get(id=1)  # Margherita Pizza (9.99)
        dish2 = Dish.objects.get(id=2)  # Pepperoni Pizza (11.99)
        order = OrderService.create(
            table_number=1,
            dishes=[{"dish_id": dish1.id}, {"dish_id": dish2.id}],
        )
        self.assertEqual(order.table_number, 1)
        self.assertEqual(order.status, OrderStatus.STATUS_PENDING)
        self.assertEqual(order.total_price, Decimal("21.98"))  # 9.99 + 12.99
        self.assertEqual(order.order_dishes.count(), 2)

        # * Step 2: Update the order's dishes
        updated_order = OrderService.modify_dishes_by_id(
            order.id,
            [
                {"dish_id": dish1.id, "quantity": 2},
                {"dish_id": dish2.id},
            ],  # 2x Margherita, 1x Pepperoni
        )
        self.assertEqual(
            updated_order.total_price, Decimal("31.97")
        )  # (9.99 * 2) + 12.99
        self.assertEqual(updated_order.order_dishes.count(), 2)

        # * Step 3: Update the order's status to "ready"
        updated_order = OrderService.modify_status_by_id(
            order.id, OrderStatus.STATUS_READY
        )
        self.assertEqual(updated_order.status, OrderStatus.STATUS_READY)

        # * Step 4: Update the order's status to "paid"
        updated_order = OrderService.modify_status_by_id(
            order.id, OrderStatus.STATUS_PAID
        )
        self.assertEqual(updated_order.status, OrderStatus.STATUS_PAID)

        # * Step 5: Verify the revenue calculation
        profit = OrderService.calculate_profit()
        self.assertAlmostEqual(profit, Decimal("31.97"))

        # * Step 6: Delete the order
        deleted_count = OrderService.remove_by_id(order.id)
        # ? Three objects actually to be deleted - one for the order itself,
        # ? two for OrderDish relations
        self.assertEqual(deleted_count, 3)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

        # * Step 7: Verify the revenue calculation after deletion
        profit = OrderService.calculate_profit()
        self.assertAlmostEqual(profit, Decimal("0"))
