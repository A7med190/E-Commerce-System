from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from users.views import RegisterView, ProfileView, PasswordChangeView, AddressViewSet
from products.views import CategoryViewSet, ProductViewSet, ProductCustomizationManageView, InventoryViewSet
from cart.views import CartView, CartItemViewSet
from orders.views import OrderViewSet, OrderAdminViewSet
from payments.views import CreatePaymentIntentView, StripeWebhookView, PaymentListView
from reviews.views import ReviewViewSet, ReviewModerateView
from wishlist.views import WishlistView, WishlistItemViewSet
from search.views import SearchView, RecommendationsView
from core.health import health_check_registry, HealthCheckSerializer
from django.http import JsonResponse

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart/items', CartItemViewSet, basename='cartitem')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'admin/orders', OrderAdminViewSet, basename='admin-order')
router.register(r'admin/inventory', InventoryViewSet, basename='inventory')
router.register(r'wishlist/items', WishlistItemViewSet, basename='wishlistitem')
router.register(r'products/(?P<product_id>[^/.]+)/reviews', ReviewViewSet, basename='product-review')
router.register(r'reviews', ReviewViewSet, basename='review')


def health_check_view(request):
    result = health_check_registry.run_all()
    serializer = HealthCheckSerializer(result)
    status = 200 if result['status'] == 'healthy' else 503
    return JsonResponse(serializer.data, status=status)


urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(), name='redoc'),

    path('api/health/', health_check_view, name='health-check'),

    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', ProfileView.as_view(), name='profile'),
    path('api/auth/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('api/users/me/addresses/', AddressViewSet.as_view({'get': 'list', 'post': 'create'}), name='address-list'),
    path('api/users/me/addresses/<uuid:pk>/', AddressViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='address-detail'),

    path('api/cart/', CartView.as_view(), name='cart'),

    path('api/payments/create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('api/payments/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/payments/', PaymentListView.as_view(), name='payment-list'),

    path('api/admin/reviews/<uuid:pk>/moderate/', ReviewModerateView.as_view(), name='review-moderate'),
    path('api/admin/products/<uuid:product_id>/customizations/', ProductCustomizationManageView.as_view(), name='product-customization-manage'),

    path('api/wishlist/', WishlistView.as_view(), name='wishlist'),

    path('api/search/', SearchView.as_view(), name='search'),
    path('api/recommendations/', RecommendationsView.as_view(), name='recommendations'),

    path('ws/', include('core.websocket_urls')),
    path('sse/', include('core.sse_urls')),

    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
