# E-Commerce System

A comprehensive REST API for managing e-commerce operations including products, orders, cart, payments, reviews, and wishlist.

## Tech Stack

- **Backend**: Django 5.0 + Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Payments**: Stripe
- **API Docs**: drf-spectacular (OpenAPI 3.0 / Swagger)
- **Testing**: pytest + pytest-django + factory-boy
- **Deployment**: Docker + Docker Compose

## Project Structure

```
├── ecommerce_backend/
│   ├── core/               # Shared utilities (permissions, pagination, models)
│   ├── users/              # User authentication, profiles
│   ├── products/           # Product CRUD, categories, images
│   ├── orders/            # Order management, workflow
│   ├── cart/               # Shopping cart
│   ├── payments/          # Stripe integration, webhooks
│   ├── reviews/            # Product reviews, ratings
│   ├── wishlist/           # User wishlists
│   ├── search/             # Product search
│   ├── ecommerce_backend/ # Django settings (base/dev/prod)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── manage.py
```

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## Local Setup (Without Docker)

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials and other settings
```

### 4. Create PostgreSQL database

```sql
CREATE DATABASE ecommerce_db;
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create superuser

```bash
python manage.py createsuperuser
```

### 7. Run development server

```bash
python manage.py runserver
```

## Docker Setup

```bash
cd ecommerce_backend
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/v1/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/schema/`

## Authentication

### 1. Register User
```bash
POST /api/v1/users/register/
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 2. Login (Get Token)
```bash
POST /api/v1/auth/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 3. Refresh Token
```bash
POST /api/v1/auth/token/refresh/
{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

## API Endpoints

### Authentication
- `POST /api/v1/users/register/` - Register new user
- `POST /api/v1/auth/login/` - Login (get tokens)
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `POST /api/v1/auth/logout/` - Logout (blacklist token)

### Products
- `GET /api/v1/products/` - List products (with pagination, filters)
- `POST /api/v1/products/` - Create product (admin)
- `GET /api/v1/products/<id>/` - Get product details
- `PUT /api/v1/products/<id>/` - Update product (admin)
- `DELETE /api/v1/products/<id>/` - Delete product (admin)
- `GET /api/v1/products/categories/` - List categories
- `POST /api/v1/products/<id>/images/` - Upload product images

### Orders
- `GET /api/v1/orders/` - List user orders
- `POST /api/v1/orders/` - Create order from cart
- `GET /api/v1/orders/<id>/` - Get order details
- `PUT /api/v1/orders/<id>/cancel/` - Cancel order
- `POST /api/v1/orders/<id>/status/` - Update order status

### Cart
- `GET /api/v1/cart/` - Get cart items
- `POST /api/v1/cart/add/` - Add item to cart
- `PUT /api/v1/cart/update/<id>/` - Update cart item quantity
- `DELETE /api/v1/cart/remove/<id>/` - Remove item from cart
- `DELETE /api/v1/cart/clear/` - Clear cart

### Payments
- `POST /api/v1/payments/create-payment/` - Create Stripe payment
- `POST /api/v1/payments/webhook/` - Stripe webhook handler
- `GET /api/v1/payments/<id>/` - Get payment status
- `POST /api/v1/payments/<id>/refund/` - Refund payment (admin)

### Reviews
- `GET /api/v1/reviews/product/<product_id>/` - Get product reviews
- `POST /api/v1/reviews/` - Create review
- `PUT /api/v1/reviews/<id>/` - Update review
- `DELETE /api/v1/reviews/<id>/` - Delete review

### Wishlist
- `GET /api/v1/wishlist/` - Get user wishlist
- `POST /api/v1/wishlist/add/<product_id>/` - Add to wishlist
- `DELETE /api/v1/wishlist/remove/<product_id>/` - Remove from wishlist

### Search
- `GET /api/v1/search/products/?q=query` - Search products

## User Roles

| Role | Permissions |
|---|---|
| `ADMIN` | Full access to everything |
| `STAFF` | Manage products, view orders |
| `CUSTOMER` | Browse, order, review |

## Running Tests

```bash
pytest
pytest --cov=. --cov-report=html
pytest -v -k test_product
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `ecommerce_db` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `postgres` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://127.0.0.1:6379/0` |
| `STRIPE_SECRET_KEY` | Stripe secret key | - |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | - |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | - |

## Deployment

Production deployment with:
- Gunicorn (4 workers)
- PostgreSQL 15
- Redis 7

## License

MIT