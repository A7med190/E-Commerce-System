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
        username='testuser',
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
    return Product.objects.create(
        name='Test Product',
        slug='test-product',
        description='Test Description',
        price=99.99,
        category=category,
        stock=10
    )


@pytest.mark.django_db
class TestCategoryViewSet:
    def test_list_categories(self, api_client, category):
        url = '/api/categories/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_category_authenticated(self, authenticated_client):
        url = '/api/categories/'
        data = {'name': 'New Category', 'slug': 'new-category'}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
class TestProductViewSet:
    def test_list_products(self, api_client, product):
        url = '/api/products/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_product(self, api_client, product):
        url = f'/api/products/{product.id}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_product_authenticated(self, authenticated_client, category):
        url = '/api/products/'
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'description': 'Description',
            'price': 49.99,
            'category': str(category.id),
            'stock': 5
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN]
