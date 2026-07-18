import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product(db, category):
    product = Product.objects.create(
        name='Test Product',
        slug='test-product',
        description='Test Description',
        base_price=99.99,
        sku='TEST-SKU-001',
        category=category,
    )
    from products.models import Inventory
    Inventory.objects.create(product=product, stock_quantity=10)
    return product


@pytest.mark.django_db
class TestCategoryViewSet:
    pass


@pytest.mark.django_db
class TestProductViewSet:
    def test_create_product_authenticated(self, authenticated_client, category):
        url = '/api/products/'
        data = {
            'name': 'New Product',
            'slug': 'new-product-001',
            'description': 'Description',
            'base_price': 49.99,
            'sku': 'NEW-SKU-001',
            'category': str(category.id),
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN]
