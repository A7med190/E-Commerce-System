from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, Inventory
from wishlist.models import Wishlist, WishlistItem

User = get_user_model()


class WishlistAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='wishlist@test.com', password='testpass123', first_name='Wishlist', last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.product = Product.objects.create(
            name='Wishlist Product', slug='wishlist-product', description='Test',
            base_price=50.00, sku='WISH-001', category=self.category, is_active=True
        )
        Inventory.objects.create(product=self.product, stock_quantity=100)

    def test_get_wishlist(self):
        response = self.client.get('/api/wishlist/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_to_wishlist(self):
        response = self.client.post('/api/wishlist/items/', {'product_id': str(self.product.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WishlistItem.objects.count(), 1)

    def test_duplicate_wishlist_item(self):
        self.client.post('/api/wishlist/items/', {'product_id': str(self.product.id)}, format='json')
        response = self.client.post('/api/wishlist/items/', {'product_id': str(self.product.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_from_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user)
        item = WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        response = self.client.delete(f'/api/wishlist/items/{item.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WishlistItem.objects.count(), 0)
