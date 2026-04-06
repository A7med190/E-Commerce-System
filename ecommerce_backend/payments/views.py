import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Payment
from .serializers import PaymentSerializer, PaymentIntentSerializer
from orders.models import Order, OrderStatusHistory

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentIntentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data['order_id']
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total * 100),
                currency='usd',
                metadata={'order_id': str(order.id), 'order_number': order.order_number},
            )
            Payment.objects.create(
                order=order,
                amount=order.total,
                method='stripe',
                status='pending',
                stripe_payment_intent_id=intent.id,
            )
            return Response({'client_secret': intent.client_secret, 'payment_intent_id': intent.id}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            order_id = intent['metadata'].get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.status = 'confirmed'
                    order.save()
                    OrderStatusHistory.objects.create(order=order, status='confirmed', notes='Payment confirmed via Stripe')
                    payment = Payment.objects.filter(stripe_payment_intent_id=intent['id']).first()
                    if payment:
                        payment.status = 'completed'
                        payment.stripe_charge_id = intent.get('latest_charge', '')
                        payment.paid_at = timezone.now()
                        payment.save()
                    self._deduct_inventory(order)
                except Order.DoesNotExist:
                    pass
        elif event['type'] == 'payment_intent.payment_failed':
            intent = event['data']['object']
            order_id = intent['metadata'].get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.status = 'cancelled'
                    order.save()
                    OrderStatusHistory.objects.create(order=order, status='cancelled', notes='Payment failed')
                    payment = Payment.objects.filter(stripe_payment_intent_id=intent['id']).first()
                    if payment:
                        payment.status = 'failed'
                        payment.save()
                except Order.DoesNotExist:
                    pass
        return Response({'received': True})

    def _deduct_inventory(self, order):
        from products.models import Inventory
        for item in order.items.all():
            try:
                inventory = Inventory.objects.get(product=item.product)
                inventory.stock_quantity = max(0, inventory.stock_quantity - item.quantity)
                inventory.save()
            except Inventory.DoesNotExist:
                pass


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).select_related('order')
