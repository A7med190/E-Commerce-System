import factory
import faker
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order, OrderItem
from reviews.models import Review

fake = faker.Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')
    description = factory.Faker('paragraph')
    is_active = True


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f'Product {n}')
    slug = factory.Sequence(lambda n: f'product-{n}')
    description = factory.Faker('paragraph')
    base_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, min_value=1, max_value=999)
    sku = factory.Sequence(lambda n: f'SKU-{n:06d}')
    category = factory.SubFactory(CategoryFactory)
    is_active = True
    is_featured = False


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'
    subtotal = factory.Faker('pydecimal', left_digits=4, right_digits=2)
    tax = factory.Faker('pydecimal', left_digits=3, right_digits=2)
    shipping_cost = factory.Faker('pydecimal', left_digits=2, right_digits=2)
    total = factory.LazyAttribute(lambda obj: obj.subtotal + obj.tax + obj.shipping_cost)
    shipping_address = {
        'street': fake.street_address(),
        'city': fake.city(),
        'state': fake.state(),
        'zip_code': fake.zipcode(),
        'country': 'USA',
    }


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    product_name = factory.LazyAttribute(lambda obj: obj.product.name)
    product_price = factory.LazyAttribute(lambda obj: obj.product.base_price)
    quantity = factory.Faker('random_int', min=1, max=5)
    customizations = []
    total = factory.LazyAttribute(lambda obj: obj.product_price * obj.quantity)


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    user = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    rating = factory.Faker('random_int', min=1, max=5)
    title = factory.Faker('sentence', nb_words=6)
    comment = factory.Faker('paragraph')
    is_approved = True
    is_verified = True
