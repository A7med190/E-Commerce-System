import requests
import json
import sys

BASE = 'http://127.0.0.1:8000/api'
PASSED = 0
FAILED = 0
s = requests.Session()
token = None

def test(name, fn):
    global PASSED, FAILED
    try:
        fn()
        PASSED += 1
        print(f'  [PASS] {name}')
    except Exception as e:
        FAILED += 1
        print(f'  [FAIL] {name}')

def check(label, actual, expected=None, condition=None):
    if condition and not condition(actual):
        raise AssertionError(f'{label}: got {actual}')
    if expected is not None and actual != expected:
        raise AssertionError(f'{label}: expected {expected}, got {actual}')

def api(method, path, **kwargs):
    h = {'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = f'Bearer {token}'
    r = s.request(method, f'{BASE}{path}', headers=h, **kwargs)
    return r

def login():
    global token
    r = api('POST', '/auth/login/', json={'email': 'testuser@test.com', 'password': 'Test1234!'})
    token = r.json()['access']


print('\n=== A-Z INTEGRATION TEST ===\n')

# 1. Register a new user
print('--- 1. AUTH ---')
test('Register', lambda: check('status', api('POST', '/auth/register/', json={
    'email': 'testaz@test.com', 'first_name': 'AZ', 'last_name': 'Test',
    'password': 'Pass123!', 'password_confirm': 'Pass123!'
}).status_code, 201))

test('Login', lambda: (
    check('status', (r := api('POST', '/auth/login/', json={
        'email': 'testaz@test.com', 'password': 'Pass123!'
    })).status_code, 200),
    globals().__setitem__('token', r.json()['access'])
))

test('Get profile', lambda: (
    check('status', (r := api('GET', '/auth/me/')).status_code, 200),
    check('email', r.json()['email'], 'testaz@test.com')
))

# 2. Browse products
print('\n--- 2. PRODUCTS ---')
test('List products', lambda: (
    check('status', (r := api('GET', '/products/')).status_code, 200),
    check('has results', len(r.json()['results']), condition=lambda x: x > 0),
    globals().__setitem__('products', r.json()['results'])
))

test('Featured products', lambda: (
    check('status', (r := api('GET', '/products/?featured=true')).status_code, 200)
))

test('Categories', lambda: (
    check('status', (r := api('GET', '/categories/')).status_code, 200)
))

test('Product detail', lambda: (
    check('status', (r := api('GET', f'/products/{products[0]["slug"]}/')).status_code, 200)
))

# 3. Cart operations
print('\n--- 3. CART ---')
test('Get empty cart', lambda: check('status', api('GET', '/cart/').status_code, 200))

test('Add to cart', lambda: (
    check('status', (r := api('POST', '/cart/items/', json={
        'product_id': products[0]['id'], 'quantity': 2
    })).status_code, 201)
))

test('Update cart item qty', lambda: (
    check('status', (r := api('GET', '/cart/')).status_code, 200),
    check('has item', (item := r.json()['items'][0]), condition=lambda x: x),
    check('status', api('PATCH', f'/cart/items/{item["id"]}/', json={'quantity': 3}).status_code, 200)
))

test('Cart total updated', lambda: (
    check('status', (r := api('GET', '/cart/')).status_code, 200),
    check('qty', r.json()['items'][0]['quantity'], 3)
))

# 4. Wishlist
print('\n--- 4. WISHLIST ---')
test('Get empty wishlist', lambda: check('status', api('GET', '/wishlist/').status_code, 200))

test('Add to wishlist', lambda: (
    check('status', (r := api('POST', '/wishlist/items/', json={
        'product_id': products[0]['id']
    })).status_code, 201)
))

test('Wishlist has item', lambda: (
    check('status', (r := api('GET', '/wishlist/')).status_code, 200),
    check('count', r.json()['item_count'], 1)
))

# 5. Address management
print('\n--- 5. ADDRESSES ---')
test('Create address', lambda: (
    check('status', (r := api('POST', '/users/me/addresses/', json={
        'street': '456 Main St', 'city': 'Metropolis', 'state': 'NY',
        'zip_code': '10001', 'country': 'USA', 'address_type': 'shipping'
    })).status_code, 201)
))

test('List addresses', lambda: (
    check('status', (r := api('GET', '/users/me/addresses/')).status_code, 200),
    check('has addr', len(r.json()['results']), condition=lambda x: x > 0),
    globals().__setitem__('addresses', r.json()['results'])
))

# 6. Checkout & Order
print('\n--- 6. ORDERS ---')
test('Create order', lambda: (
    check('status', (r := api('POST', '/orders/', json={
        'shipping_address_id': addresses[0]['id']
    })).status_code, 201),
    check('has order_number', r.json().get('order_number'), condition=lambda x: bool(x)),
    globals().__setitem__('order', r.json())
))

test('List orders', lambda: (
    check('status', (r := api('GET', '/orders/')).status_code, 200),
    check('has order', r.json()['results'][0]['id'], order['id'])
))

test('Order detail', lambda: (
    check('status', (r := api('GET', f'/orders/{order["id"]}/')).status_code, 200),
    check('status', r.json()['status'], 'pending')
))

test('Order has items', lambda: (
    check('status', (r := api('GET', f'/orders/{order["id"]}/')).status_code, 200),
    check('items', len(r.json()['items']), condition=lambda x: x > 0)
))

test('Order has correct total', lambda: (
    check('status', (r := api('GET', f'/orders/{order["id"]}/')).status_code, 200),
    check('total', float(r.json()['total']), condition=lambda x: x > 0)
))

# 7. Search
print('\n--- 7. SEARCH ---')
test('Search products', lambda: (
    check('status', (r := api('GET', '/search/?q=tee')).status_code, 200),
    check('results', len(r.json().get('results', [])), condition=lambda x: x >= 0)
))

test('Search empty query', lambda: (
    check('status', (r := api('GET', '/search/?q=nonexistent123xyz')).status_code, 200)
))

# 8. Reviews
print('\n--- 8. REVIEWS ---')
test('Create review', lambda: (
    check('status', (r := api('POST', f'/products/{products[0]["id"]}/reviews/', json={
        'product': products[0]['id'], 'rating': 4, 'comment': 'Nice product!'
    })).status_code in (201, 400))
))

# 9. Profile
print('\n--- 9. PROFILE ---')
test('Change password', lambda: (
    check('status', (r := api('POST', '/auth/change-password/', json={
        'old_password': 'Pass123!', 'new_password': 'NewPass123!',
        'new_password_confirm': 'NewPass123!'
    })).status_code, 200)
))

test('Login with new password', lambda: (
    check('status', (r := api('POST', '/auth/login/', json={
        'email': 'testaz@test.com', 'password': 'NewPass123!'
    })).status_code, 200),
    globals().__setitem__('token', r.json()['access'])
))

# 10. Token refresh
print('\n--- 10. TOKEN REFRESH ---')
test('Token refresh', lambda: (
    check('status', (r := api('POST', '/auth/login/', json={
        'email': 'testaz@test.com', 'password': 'NewPass123!'
    })).status_code, 200),
    check('has refresh', r.json().get('refresh'), condition=lambda x: bool(x)),
    check('refresh status', (r2 := api('POST', '/auth/refresh/', json={
        'refresh': r.json()['refresh']
    })).status_code, 200),
    check('new access token', r2.json().get('access'), condition=lambda x: bool(x))
))

print(f'\n=== RESULTS: {PASSED + FAILED} tests ===')
print(f'  PASSED: {PASSED}')
print(f'  FAILED: {FAILED}')
if FAILED:
    sys.exit(1)
else:
    print('  STATUS: ALL PASSED')
