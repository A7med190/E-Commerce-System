import uuid
import random
import string
from decimal import Decimal
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def generate_order_number():
    prefix = 'ORD'
    timestamp_part = str(uuid.uuid4())[:8].upper()
    random_part = ''.join(random.choices(string.digits, k=6))
    return f'{prefix}-{timestamp_part}-{random_part}'


def generate_slug(text):
    import re
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug


def calculate_customization_price(base_price, customizations, customization_values):
    total_modifier = Decimal('0')
    for cust in customizations:
        value_id = cust.get('value_id')
        if value_id:
            value = customization_values.filter(id=value_id).first()
            if value:
                if value.modifier_type == 'fixed':
                    total_modifier += value.price_modifier
                elif value.modifier_type == 'percent':
                    total_modifier += base_price * (value.price_modifier / Decimal('100'))
    return base_price + total_modifier


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        error_messages = {
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            409: 'Conflict',
            429: 'Too Many Requests',
            500: 'Internal Server Error',
        }
        custom_response = {
            'status_code': response.status_code,
            'error': error_messages.get(response.status_code, 'Error'),
            'detail': response.data if isinstance(response.data, dict) else {'message': response.data},
        }
        response.data = custom_response
    return response
