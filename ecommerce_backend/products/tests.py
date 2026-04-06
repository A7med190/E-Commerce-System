from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, Inventory, CustomizationOption, CustomizationValue, ProductCustomization
from cart.models import Cart, CartItem

User = get_user_model()


class ProductAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@test.com', password='adminpass123', first_name='Admin', last_name='User'
        )
        self.category = Category.objects.create(name='Electronics', slug='electronics', is_active=True)
        self.product = Product.objects.create(
            name='Test Product', slug='test-product', description='A test product',
            base_price=99.99, sku='TEST-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product, stock_quantity=50)

    def test_list_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_product_detail(self):
        response = self.client.get(f'/api/products/{self.product.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')

    def test_filter_by_category(self):
        response = self.client.get('/api/products/', {'category': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_products(self):
        response = self.client.get('/api/products/', {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class CartAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='cart@test.com', password='testpass123', first_name='Cart', last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.product = Product.objects.create(
            name='Cart Product', slug='cart-product', description='Test',
            base_price=50.00, sku='CART-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product, stock_quantity=100)
        self.cart = Cart.objects.create(user=self.user)

    def test_get_cart(self):
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)

    def test_add_to_cart(self):
        response = self.client.post('/api/cart/items/', {
            'product_id': str(self.product.id),
            'quantity': 2,
            'customizations': [],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.cart.items.count(), 1)

    def test_update_cart_item(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1, customizations=[], price_at_add=50.00)
        response = self.client.patch(f'/api/cart/items/{item.id}/', {'quantity': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_remove_cart_item(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1, customizations=[], price_at_add=50.00)
        response = self.client.delete(f'/api/cart/items/{item.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.cart.items.count(), 0)

    def test_clear_cart(self):
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1, customizations=[], price_at_add=50.00)
        response = self.client.delete('/api/cart/clear/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart.items.count(), 0)
