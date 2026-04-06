from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, Inventory
from reviews.models import Review

User = get_user_model()


class ReviewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='review@test.com', password='testpass123', first_name='Review', last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.product = Product.objects.create(
            name='Review Product', slug='review-product', description='Test',
            base_price=50.00, sku='REV-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product, stock_quantity=100)

    def test_create_review(self):
        response = self.client.post(f'/api/products/{self.product.id}/reviews/', {
            'rating': 5,
            'comment': 'Great product!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_list_reviews(self):
        Review.objects.create(user=self.user, product=self.product, rating=4, comment='Good', is_approved=True)
        response = self.client.get(f'/api/products/{self.product.id}/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
