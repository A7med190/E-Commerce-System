from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, Inventory
from users.models import Address
from faker import Faker
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create admin user
        if not User.objects.filter(email='admin@ecommerce.com').exists():
            admin = User.objects.create_superuser(
                email='admin@ecommerce.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            self.stdout.write(f'Created admin: {admin.email}')

        # Create test users
        for i in range(5):
            email = f'user{i+1}@example.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='password123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    role='customer'
                )
                # Add addresses
                Address.objects.create(
                    user=user,
                    address_type='shipping',
                    street=fake.street_address(),
                    city=fake.city(),
                    state=fake.state(),
                    zip_code=fake.zipcode(),
                    country=fake.country(),
                    is_default=True
                )

        # Create categories
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
        category_objects = []
        for cat in categories:
            category, _ = Category.objects.get_or_create(
                name=cat,
                slug=cat.lower().replace(' ', '-')
            )
            category_objects.append(category)

        self.stdout.write(f'Created {len(category_objects)} categories')

        # Create products
        product_names = [
            'Wireless Headphones', 'Smart Watch', 'Laptop Stand', 'USB Cable',
            'T-Shirt', 'Jeans', 'Sneakers', 'Jacket',
            'Plant Pot', 'Wall Clock', 'Desk Lamp', 'Cushion',
            'Yoga Mat', 'Dumbbells', 'Running Shoes', 'Water Bottle',
            'Programming Guide', 'Novel', 'Cookbook', 'Art Book',
            'Building Blocks', 'Puzzle', 'Remote Control Car', 'Board Game'
        ]

        for name in product_names:
            category = random.choice(category_objects)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'slug': name.lower().replace(' ', '-'),
                    'description': fake.text(max_nb_chars=200),
                    'base_price': round(random.uniform(10, 500), 2),
                    'sku': f'SKU-{random.randint(1000, 9999)}',
                    'category': category,
                    'is_active': True,
                    'is_featured': random.choice([True, False])
                }
            )
            if created:
                Inventory.objects.create(
                    product=product,
                    stock_quantity=random.randint(0, 100),
                    low_stock_threshold=10
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))