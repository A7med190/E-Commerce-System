import os
import sys
import django
from django.conf import settings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings.development')

def pytest_configure():
    django.setup()
