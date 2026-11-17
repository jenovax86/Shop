import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from addresses.models import Address
from carts.models import Carts
from categories.models import Category
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from products.models import Product
from sessions.models import Session
from users.models import User

MEDIA = 'application/vnd.api+json'


def linkage(resource_type, obj):
    return {'type': resource_type, 'id': str(obj.pk)}


def document(resource_type, attributes=None, relationships=None, pk=None):
    data = {'type': resource_type}
    if pk is not None:
        data['id'] = str(pk)
    if attributes is not None:
        data['attributes'] = attributes
    if relationships:
        data['relationships'] = {name: {'data': value} for name, value in relationships.items()}
    return {'data': data}


class JSONAPIApplicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username='owner', password='test-password')
        cls.other = User.objects.create_user(username='other', password='test-password')
        cls.admin = User.objects.create_user(username='admin', password='test-password', role='admin')
        cls.category = Category.objects.create(name='shirt')
        cls.product = Product.objects.create(category=cls.category, name='shirt', size='small', color='red', price=20)
        cls.address = Address.objects.create(user=cls.owner, country='country', city='city', province='province',
                                             zip_code='123')
        cls.other_address = Address.objects.create(user=cls.other, country='country', city='city', province='province',
                                                   zip_code='123')
        cls.cart = Carts.objects.create(user=cls.owner, product=cls.product, quantity=2, size='small', color='red')
        cls.coupon = Coupon.objects.create(user=cls.owner, percentage=10)
        cls.other_coupon = Coupon.objects.create(user=cls.other, percentage=15)
        cls.order = Order.objects.create(user=cls.owner, address=cls.address, price=40, discounted_price=40,
                                         state='pending')

    def client_for(self, user=None):
        client = APIClient(HTTP_ACCEPT=MEDIA)
        if user:
            refresh = RefreshToken.for_user(user)
            session = Session.objects.create(user=user, user_agent='test',
                                             expires_at=timezone.now() + timedelta(days=1), refresh_jti=refresh['jti'])
            refresh['sid'] = session.pk
            client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
            client.cookies['refresh'] = str(refresh)
        return client

    def send(self, client, method, path, resource_type, attributes=None, relationships=None, pk=None):
        return getattr(client, method)(path, json.dumps(document(resource_type, attributes, relationships, pk)),
                                       content_type=MEDIA, HTTP_ACCEPT=MEDIA)

    def assert_document(self, response, status=200):
        self.assertEqual(response.status_code, status, response.content)
        self.assertEqual(response['Content-Type'], MEDIA)
        body = response.json()
        self.assertTrue(set(body) & {'data', 'errors', 'meta'}, body)
        self.assertFalse('data' in body and 'errors' in body, body)
        self.assertNotIn('success', body)
        self.assertNotIn('status_code', body)
        return body

    def assert_error(self, response, status):
        body = self.assert_document(response, status)
        self.assertIsInstance(body['errors'], list)
        self.assertTrue(body['errors'])
        self.assertTrue(all(error['status'] == str(status) for error in body['errors']))
        return body

    def test_public_resource_documents_and_pagination(self):
        client = self.client_for()
        for resource, obj in [('categories', self.category), ('products', self.product)]:
            with self.subTest(resource=resource):
                body = self.assert_document(client.get(f'/api/v1/{resource}/'))
                self.assertIsInstance(body['data'], list)
                self.assertEqual(body['data'][0]['type'], resource)
                self.assertEqual(body['data'][0]['id'], str(obj.pk))
                self.assertIn('attributes', body['data'][0])
                self.assertIn('pagination', body['meta'])
                self.assertEqual(set(body['links']), {'next', 'prev'})
                detail = self.assert_document(client.get(f'/api/v1/{resource}/{obj.pk}/'))
                self.assertEqual(detail['data']['id'], str(obj.pk))
        body = client.get(f'/api/v1/products/{self.product.pk}/').json()
        self.assertEqual(body['data']['relationships']['category']['data'], linkage('categories', self.category))

    def test_admin_resource_create_update_and_permissions(self):
        anonymous, member, admin = self.client_for(), self.client_for(self.owner), self.client_for(self.admin)
        for client, status in [(anonymous, 401), (member, 403)]:
            self.assert_error(self.send(client, 'post', '/api/v1/categories/', 'categories', {'name': 'hoodie'}),
                              status)
        body = self.assert_document(self.send(admin, 'post', '/api/v1/categories/', 'categories', {'name': 'hoodie'}),
                                    201)
        self.assertEqual(body['data']['attributes']['name'], 'hoodie')
        response = self.send(admin, 'post', '/api/v1/products/', 'products',
                             {'name': 'new', 'size': 'small', 'color': 'red', 'price': '10.00'},
                             {'category': linkage('categories', self.category)})
        body = self.assert_document(response, 201)
        self.assertEqual(response['Location'], body['data']['links']['self'])
        product = Product.objects.get(pk=body['data']['id'])
        self.assertEqual(product.category_id, self.category.pk)
        body = self.assert_document(
            self.send(admin, 'patch', f'/api/v1/products/{product.pk}/', 'products', {'name': 'updated'},
                      pk=product.pk))
        self.assertEqual(body['data']['attributes']['name'], 'updated')
        self.assert_error(self.send(member, 'patch', f'/api/v1/products/{product.pk}/', 'products', {'name': 'attack'},
                                    pk=product.pk), 403)
        response = admin.delete(f'/api/v1/products/{product.pk}/', HTTP_ACCEPT=MEDIA)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"meta": {"message": "Deleted successfully."}})
        self.assert_error(anonymous.get(f'/api/v1/products/{product.pk}/'), 404)

    def test_jsonapi_relationship_create_and_owner_reassignment(self):
        owner, admin = self.client_for(self.owner), self.client_for(self.admin)
        attrs = {'country': 'country', 'city': 'city', 'province': 'province', 'zip_code': '123'}
        for client, expected in [(owner, self.owner), (admin, self.other)]:
            body = self.assert_document(self.send(client, 'post', '/api/v1/addresses/', 'addresses', attrs,
                                                  {'user': linkage('users', self.other)}), 201)
            self.assertEqual(body['data']['relationships']['user']['data'], linkage('users', expected))
        for client, expected in [(owner, self.owner), (admin, self.other)]:
            body = self.assert_document(self.send(client, 'post', '/api/v1/carts/', 'carts', {'quantity': 1},
                                                  {'user': linkage('users', self.other),
                                                   'product': linkage('products', self.product)}), 201)
            self.assertEqual(body['data']['relationships']['user']['data'], linkage('users', expected))
        self.assert_document(self.send(owner, 'patch', f'/api/v1/addresses/{self.address.pk}/', 'addresses',
                                       relationships={'user': linkage('users', self.other)}, pk=self.address.pk))
        self.address.refresh_from_db()
        self.assertEqual(self.address.user_id, self.owner.pk)
        self.assert_document(self.send(admin, 'patch', f'/api/v1/addresses/{self.address.pk}/', 'addresses',
                                       relationships={'user': linkage('users', self.other)}, pk=self.address.pk))
        self.address.refresh_from_db()
        self.assertEqual(self.address.user_id, self.other.pk)

    def test_personal_resources_are_private_and_admin_can_manage(self):
        anon, owner, other, admin = self.client_for(), self.client_for(self.owner), self.client_for(
            self.other), self.client_for(self.admin)
        for resource in ['users', 'addresses', 'carts', 'orders', 'coupons', 'auth/sessions']:
            self.assert_error(anon.get(f'/api/v1/{resource}/'), 401)
        for resource, obj, attrs in [('addresses', self.address, {'city': 'updated'}),
                                     ('carts', self.cart, {'quantity': 3}), ('orders', self.order, {})]:
            with self.subTest(resource=resource):
                url = f'/api/v1/{resource}/{obj.pk}/'
                self.assert_document(owner.get(url))
                self.assert_error(other.get(url), 404)
                self.assert_error(self.send(other, 'patch', url, resource, attrs, pk=obj.pk), 404)
                self.assert_error(other.delete(url), 404)
                self.assert_document(self.send(admin, 'patch', url, resource, attrs, pk=obj.pk))
                self.assertEqual(owner.delete(url).status_code, 200)
                self.assert_error(owner.get(url), 404)
                self.assert_document(admin.get(url))
                self.assert_document(self.send(admin, 'patch', url, resource, {'deleted_at': None}, pk=obj.pk))
                self.assert_document(owner.get(url))

    def test_order_relationship_constraints_and_items(self):
        owner = self.client_for(self.owner)
        self.assert_error(self.send(owner, 'post', '/api/v1/orders/', 'orders',
                                    relationships={'address': linkage('addresses', self.other_address)}), 400)
        self.assert_error(self.send(owner, 'post', '/api/v1/orders/', 'orders',
                                    relationships={'address': linkage('addresses', self.address),
                                                   'coupon': linkage('coupons', self.other_coupon)}), 400)
        body = self.assert_document(
            self.send(owner, 'post', '/api/v1/orders/', 'orders', {'price': '0.01', 'state': 'delivered'},
                      {'address': linkage('addresses', self.address), 'user': linkage('users', self.other)}), 201)
        order = Order.objects.get(pk=body['data']['id'])
        self.assertEqual(order.user_id, self.owner.pk)
        self.assertEqual(order.price, Decimal('40.00'))
        self.assertEqual(order.state, 'pending')
        self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)
        item = order.orderproduct_set.get()
        self.assertEqual(body['data']['relationships']['items']['data'], [linkage('order-products', item)])
        included = self.assert_document(owner.get(f'/api/v1/orders/{order.pk}/?include=items.product'))
        self.assertEqual({row['type'] for row in included['included']}, {'order-products', 'products'})
        body = self.assert_document(self.send(owner, 'post', '/api/v1/orders/', 'orders',
                                              relationships={'address': linkage('addresses', self.address),
                                                             'coupon': linkage('coupons', self.coupon)}), 201)
        self.assertEqual(body['data']['attributes']['discounted_price'], '36.00')
        self.coupon.refresh_from_db()
        self.assertIsNotNone(self.coupon.used_at)
        admin = self.client_for(self.admin)
        self.assert_document(self.send(admin, 'patch', f'/api/v1/orders/{self.order.pk}/', 'orders',
                                       {'state': 'shipped', 'price': '50.00', 'discounted_price': '45.00'},
                                       {'user': linkage('users', self.other),
                                        'address': linkage('addresses', self.other_address)}, self.order.pk))
        self.order.refresh_from_db()
        self.assertEqual(self.order.user_id, self.other.pk)
        self.assertEqual(self.order.state, 'shipped')

    def test_coupon_privacy_and_admin_updates(self):
        owner, other, admin = self.client_for(self.owner), self.client_for(self.other), self.client_for(self.admin)
        body = self.assert_document(owner.get('/api/v1/coupons/'))
        self.assertEqual([row['id'] for row in body['data']], [str(self.coupon.pk)])
        self.assert_error(other.get(f'/api/v1/coupons/{self.coupon.pk}/'), 404)
        self.assert_error(self.send(owner, 'patch', f'/api/v1/coupons/{self.coupon.pk}/', 'coupons', {'percentage': 50},
                                    pk=self.coupon.pk), 403)
        self.assert_document(self.send(admin, 'patch', f'/api/v1/coupons/{self.coupon.pk}/', 'coupons',
                                       {'is_active': False, 'duration_days': 5}, pk=self.coupon.pk))
        self.coupon.refresh_from_db()
        self.assertFalse(self.coupon.is_active)
        self.assertEqual(self.coupon.duration, timedelta(days=5))
        self.assert_document(
            self.send(admin, 'post', '/api/v1/coupons/', 'coupons', {'percentage': 20, 'duration_days': 2},
                      {'user': linkage('users', self.other)}), 201)

    def test_user_privilege_boundaries_and_inactive_tokens(self):
        owner, other, admin = self.client_for(self.owner), self.client_for(self.other), self.client_for(self.admin)
        self.assert_error(
            self.send(other, 'patch', f'/api/v1/users/{self.owner.pk}/', 'users', {'password': 'attacker-password'},
                      pk=self.owner.pk), 404)
        body = self.assert_document(self.send(owner, 'patch', f'/api/v1/users/{self.owner.pk}/', 'users',
                                              {'username': 'renamed', 'password': '  new-password  ', 'role': 'admin',
                                               'is_superuser': True}, pk=self.owner.pk))
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.role, 'user')
        self.assertFalse(self.owner.is_superuser)
        self.assertTrue(self.owner.check_password('  new-password  '))
        self.assertNotIn('password', body['data']['attributes'])
        self.assert_document(
            self.send(admin, 'patch', f'/api/v1/users/{self.other.pk}/', 'users', {'role': 'admin'}, pk=self.other.pk))
        self.assertEqual(admin.delete(f'/api/v1/users/{self.owner.pk}/').status_code, 200)
        self.assert_error(owner.get('/api/v1/carts/'), 401)
        self.admin.role = 'user'
        self.admin.save(update_fields=['role'])
        self.assert_error(self.send(admin, 'post', '/api/v1/categories/', 'categories', {'name': 'hoodie'}), 403)
        self.admin.is_superuser = True
        self.admin.save(update_fields=['is_superuser'])
        self.assert_document(self.send(admin, 'post', '/api/v1/categories/', 'categories', {'name': 'hoodie'}), 201)

    def test_auth_documents_refresh_cookies_and_rotation(self):
        client = self.client_for()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid-old-token')
        body = self.assert_document(self.send(client, 'post', '/api/v1/auth/register/', 'users',
                                              {'username': 'newuser', 'password': 'test-password'}), 201)
        user = User.objects.get(username='newuser')
        self.assertEqual(body['data']['type'], 'users')
        self.assertEqual(body['data']['id'], str(user.pk))
        self.assertEqual(AccessToken(body['meta']['access'])['sub'], str(user.pk))
        body = self.assert_document(self.send(client, 'post', '/api/v1/auth/login/', 'tokens',
                                              {'username': 'newuser', 'password': 'test-password'}))
        self.assertIn('access', body['meta'])
        self.assertNotIn('data', body)
        before = client.cookies['refresh'].value
        response = client.post('/api/v1/auth/refresh/', HTTP_ACCEPT=MEDIA)
        body = self.assert_document(response)
        self.assertNotEqual(client.cookies['refresh'].value, before)
        self.assertEqual(AccessToken(body['meta']['access'])['sid'],
                         RefreshToken(client.cookies['refresh'].value)['sid'])
        cookie = response.cookies['refresh']
        self.assertTrue(cookie['httponly'])
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'Lax')
        replay = self.client_for()
        replay.cookies['refresh'] = before
        self.assert_error(replay.post('/api/v1/auth/refresh/', HTTP_ACCEPT=MEDIA), 401)
        self.assert_error(self.send(self.client_for(), 'post', '/api/v1/auth/login/', 'tokens',
                                    {'username': 'newuser', 'password': 'wrong'}), 401)
        self.assert_error(self.send(self.client_for(), 'post', '/api/v1/auth/register/', 'users',
                                    {'username': 'newuser', 'password': 'test-password'}), 409)

    def test_oauth_and_session_actions_use_standard_documents(self):
        client = self.client_for()
        with patch('auth.views.oauth.google.authorize_access_token',
                   return_value={'userinfo': {'sub': 'google-identity', 'email': 'google@example.com'}}):
            body = self.assert_document(client.get('/api/v1/auth/google/callback/'))
        access = body['meta']['access']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        self.assert_document(client.post('/api/v1/auth/refresh/', HTTP_ACCEPT=MEDIA))
        own_session = Session.objects.get(user__google_identity='google-identity')
        body = self.assert_document(client.get('/api/v1/auth/sessions/'))
        self.assertEqual(body['data'][0]['type'], 'sessions')
        other = self.client_for(self.other)
        other_session = Session.objects.get(user=self.other)
        body = self.assert_document(self.send(client, 'post', '/api/v1/auth/sessions/revoke/', 'session-revocations',
                                              {'session_ids': [other_session.pk]}))
        self.assertEqual(body['meta']['revoked_sessions'], 0)
        admin = self.client_for(self.admin)
        body = self.assert_document(self.send(admin, 'post', '/api/v1/auth/sessions/revoke/', 'session-revocations',
                                              {'session_ids': [other_session.pk]}))
        self.assertEqual(body['meta']['revoked_sessions'], 1)
        self.assert_error(other.post('/api/v1/auth/refresh/', HTTP_ACCEPT=MEDIA), 401)
        response = client.post('/api/v1/auth/sessions/logout/', HTTP_ACCEPT=MEDIA)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        own_session.refresh_from_db()
        self.assertIsNotNone(own_session.revoked_at)

    def test_include_sparse_fields_sort_filter_and_page_parameters(self):
        client = self.client_for()
        body = self.assert_document(
            client.get(f'/api/v1/products/{self.product.pk}/?include=category&fields[products]=name,category'))
        self.assertEqual(body['data']['attributes'], {'name': 'shirt'})
        self.assertEqual(body['included'][0]['type'], 'categories')
        Product.objects.create(category=self.category, name='cheap', size='small', color='blue', price=5)
        body = self.assert_document(client.get('/api/v1/products/?filter[min_price]=10&sort=price&page[size]=1'))
        self.assertEqual(len(body['data']), 1)
        self.assertEqual(body['data'][0]['id'], str(self.product.pk))
        self.assertEqual(body['meta']['pagination']['page_size'], 1)
        self.assertNotIn('count', body['meta']['pagination'])
        for query in ['unknown=1', 'sort=not_a_field', 'filter[unknown]=1', 'include=user', 'include=category.user']:
            self.assert_error(client.get('/api/v1/products/?' + query), 400)

    def test_standard_errors_and_invalid_documents(self):
        admin = self.client_for(self.admin)
        url = f'/api/v1/products/{self.product.pk}/'
        badprice = self.send(admin, 'patch', url, 'products', {'price': '-1'}, pk=self.product.pk)
        body = self.assert_error(badprice, 400)
        self.assertEqual(body['errors'][0]['source']['pointer'], '/data/attributes/price')
        self.assert_error(self.send(admin, 'patch', url, 'products', {'price': '1'}, pk=self.product.pk + 999), 409)
        self.assert_error(self.send(admin, 'post', '/api/v1/categories/', 'products', {'name': 'hoodie'}), 409)
        self.assert_error(
            self.send(admin, 'post', '/api/v1/categories/', 'categories', {'name': 'hoodie'}, pk='client-id'), 403)
        self.assert_error(self.send(admin, 'post', '/api/v1/products/', 'products', {'name': 'bad'},
                                    {'category': linkage('users', self.owner)}), 409)
        for payload in [{}, {'data': {}}, {'data': {'type': 'products', 'id': 1}},
                        {'data': {'type': 'products', 'attributes': []}}, {
                            'data': {'type': 'products', 'attributes': {'category': 'bad'},
                                     'relationships': {'category': {'data': None}}}}]:
            self.assert_error(
                admin.post('/api/v1/products/', json.dumps(payload), content_type=MEDIA, HTTP_ACCEPT=MEDIA), 400)
        self.assert_error(self.client_for().get('/api/v1/no-such-route/'), 404)
        self.assert_error(admin.post('/api/v1/categories/', '{', content_type=MEDIA, HTTP_ACCEPT=MEDIA), 400)
        self.assert_error(
            admin.patch('/api/v1/products/', json.dumps(document('products', {'name': 'bulk'})), content_type=MEDIA,
                        HTTP_ACCEPT=MEDIA), 405)
        options = self.assert_document(self.client_for().options('/api/v1/products/'))
        self.assertIn('meta', options)

    def test_media_type_negotiation(self):
        admin = self.client_for(self.admin)
        payload = json.dumps(document('categories', {'name': 'hoodie'}))
        for media in ['application/json', MEDIA + '; charset=utf-8', MEDIA + '; ext="https://example.com/unsupported"']:
            self.assert_error(admin.post('/api/v1/categories/', payload, content_type=media, HTTP_ACCEPT=MEDIA), 415)
        self.assert_error(admin.get('/api/v1/products/', HTTP_ACCEPT='application/json'), 406)
        self.assert_error(admin.get('/api/v1/products/', HTTP_ACCEPT=MEDIA + '; ext="https://example.com/unsupported"'),
                          406)
        self.assert_document(
            admin.get('/api/v1/products/', HTTP_ACCEPT=MEDIA + '; ext="https://example.com/unsupported", ' + MEDIA))
        self.assert_document(admin.get('/api/v1/products/', HTTP_ACCEPT='*/*'))

    def test_invalid_relationship_linkage_is_rejected(self):
        admin = self.client_for(self.admin)
        for identifier in [1, {"type": "categories"}, {"id": "1"}, {"type": "categories", "id": 1}]:
            self.assert_error(
                self.send(admin, "post", "/api/v1/products/", "products", {"name": "bad"}, {"category": identifier}),
                400)

    def test_internal_errors_are_sanitized_jsonapi_documents(self):
        client = self.client_for()
        with patch("auth.views.User.objects.create_user", side_effect=RuntimeError("private-debug-value")):
            with self.assertLogs("core.handlers.custom_exception_handler", level="ERROR"):
                response = self.send(client, "post", "/api/v1/auth/register/", "users",
                                     {"username": "newuser", "password": "test-password"})
        self.assert_error(response, 500)
        self.assertNotIn("private-debug-value", response.content.decode())
