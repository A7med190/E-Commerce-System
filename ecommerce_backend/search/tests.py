from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, Inventory

User = get_user_model()


class SearchAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product1 = Product.objects.create(
            name='Laptop Pro', slug='laptop-pro', description='High-end laptop',
            base_price=999.99, sku='LAP-001', category=self.category, is_active=True
        )
        self.product2 = Product.objects.create(
            name='Phone Max', slug='phone-max', description='Latest smartphone',
            base_price=699.99, sku='PHN-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product1, stock_quantity=10)
        Inventory.objects.create(product=self.product2, stock_quantity=20)

    def test_search_by_name(self):
        response = self.client.get('/api/search/', {'q': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Laptop Pro')

    def test_search_by_description(self):
        response = self.client.get('/api/search/', {'q': 'smartphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_with_price_filter(self):
        response = self.client.get('/api/search/', {'q': '', 'min_price': '700'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_sort_by_price(self):
        response = self.client.get('/api/search/', {'q': '', 'sort': 'price_asc'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['name'], 'Phone Max')
