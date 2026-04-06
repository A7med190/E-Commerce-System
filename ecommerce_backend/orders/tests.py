from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, Inventory
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from users.models import Address

User = get_user_model()


class OrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='order@test.com', password='testpass123', first_name='Order', last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.product = Product.objects.create(
            name='Order Product', slug='order-product', description='Test',
            base_price=75.00, sku='ORD-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product, stock_quantity=100)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2, customizations=[], price_at_add=75.00)
        self.address = Address.objects.create(
            user=self.user, address_type='shipping', street='123 Test St',
            city='Test City', state='TS', zip_code='12345', country='US', is_default=True
        )

    def test_create_order(self):
        response = self.client.post('/api/orders/', {
            'shipping_address_id': str(self.address.id),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(self.cart.items.count(), 0)

    def test_list_orders(self):
        self.client.post('/api/orders/', {'shipping_address_id': str(self.address.id)}, format='json')
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_order_detail(self):
        self.client.post('/api/orders/', {'shipping_address_id': str(self.address.id)}, format='json')
        order = Order.objects.first()
        response = self.client.get(f'/api/orders/{order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], order.order_number)
