import json
from copy import deepcopy

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase, TestCase
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
from rest_framework.test import APIClient

from users import tests as jsonapi_tests
from users.tests import MEDIA, document, linkage


class OpenAPIDocumentationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = SchemaGenerator().get_schema(public=True)

    def test_schema_is_valid_and_documents_every_app(self):
        validate_schema(self.schema)
        self.assertEqual(self.schema['openapi'], '3.0.3')
        for app in ['users', 'addresses', 'carts', 'orders', 'coupons', 'categories', 'products']:
            self.assertIn(f'/api/v1/{app}/', self.schema['paths'])
            self.assertIn(f'/api/v1/{app}/{{id}}/', self.schema['paths'])
        self.assertNotIn('/api/docs/', self.schema['paths'])
        self.assertNotIn('/api/schema/', self.schema['paths'])
        ids = [operation['operationId'] for path in self.schema['paths'].values() for method, operation in path.items()
               if method in ('get', 'post', 'put', 'patch', 'delete')]
        self.assertEqual(len(ids), len(set(ids)))

    def test_schema_and_swagger_ui_are_public(self):
        client = APIClient()
        response = client.get('/api/schema/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['info']['title'], 'Shop API')
        self.assertNotIn('data', response.json())
        response = client.get('/api/docs/', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, '/api/schema/')
        self.assertContains(response, 'drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js')
        self.assertContains(response, '"withCredentials": true')
        self.assertNotContains(response, 'cdn.jsdelivr.net')
        for filename in ['swagger-ui.css', 'swagger-ui-bundle.js', 'swagger-ui-standalone-preset.js']:
            self.assertIsNotNone(finders.find('drf_spectacular_sidecar/swagger-ui-dist/' + filename))

    def test_authentication_and_cookie_contracts(self):
        paths = self.schema['paths']
        for resource in ['products', 'categories']:
            self.assertFalse(paths[f'/api/v1/{resource}/']['get'].get('security'))
            self.assertEqual(paths[f'/api/v1/{resource}/']['post']['security'], [{'jwtAuth': []}])
        for resource in ['users', 'addresses', 'orders', 'carts', 'coupons']:
            self.assertEqual(paths[f'/api/v1/{resource}/']['get']['security'], [{'jwtAuth': []}])
        login = paths['/api/v1/auth/login/']['post']
        self.assertFalse(login.get('security'))
        login_body = login['requestBody']['content'][MEDIA]['schema']
        self.assertEqual(login_body['properties']['data']['properties']['type']['enum'], ['tokens'])
        self.assertIn('meta', login['responses']['200']['content'][MEDIA]['schema']['properties'])
        self.assertIn('Set-Cookie', login['responses']['200']['headers'])
        refresh = paths['/api/v1/auth/refresh/']['post']
        self.assertNotIn('requestBody', refresh)
        self.assertEqual(refresh['security'], [{'refreshCookie': []}])
        schemes = self.schema['components']['securitySchemes']
        self.assertEqual(schemes['jwtAuth']['scheme'], 'bearer')
        self.assertEqual(schemes['refreshCookie']['in'], 'cookie')
        self.assertEqual(schemes['refreshCookie']['name'], 'refresh')
        logout = paths['/api/v1/auth/sessions/logout/']['post']
        self.assertNotIn('requestBody', logout)
        self.assertNotIn('content', logout['responses']['204'])
        self.assertNotIn('content', paths['/api/v1/auth/google/login/']['get']['responses']['302'])

    def test_jsonapi_queries_and_admin_fields_are_documented(self):
        products = self.schema['paths']['/api/v1/products/']['get']
        params = {item['name']: item for item in products['parameters']}
        for name in ['page[cursor]', 'page[size]', 'sort', 'filter[min_price]', 'filter[max_price]', 'filter[category]',
                     'fields[products]', 'include']:
            self.assertIn(name, params)
        self.assertNotIn('page[number]', params)
        order_params = {item['name']: item for item in self.schema['paths']['/api/v1/orders/']['get']['parameters']}
        self.assertIn('items.product.category', order_params['include']['schema']['items']['enum'])
        user = \
            self.schema['components']['schemas']['AdminUserRequest']['properties']['data']['properties']['attributes'][
                'properties']
        self.assertIn('role', user)
        self.assertIn('is_active', user)
        response = self.schema['components']['schemas']['AdminUser']['properties']['attributes']['properties']
        self.assertNotIn('password', response)
        self.assertIn('admin-only', self.schema['paths']['/api/v1/users/{id}/']['patch']['description'])
        resource = self.schema['components']['schemas']['PatchedProductRequest']['properties']['data']
        self.assertIn('id', resource['required'])
        self.assertEqual(resource['properties']['id']['type'], 'string')


def nullable_schema(value):
    """Translate OAS 3 nullable into JSON Schema for payload validation."""
    if isinstance(value, list):
        return [nullable_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: nullable_schema(item) for key, item in value.items() if key != 'nullable'}
    if value.get('nullable') and 'type' in result:
        result['type'] = [result['type'], 'null'] if isinstance(result['type'], str) else result['type'] + ['null']
    return result


class OpenAPIWireContractTests(TestCase):
    setUpTestData = classmethod(jsonapi_tests.JSONAPIApplicationTests.setUpTestData.__func__)
    client_for = jsonapi_tests.JSONAPIApplicationTests.client_for
    send = jsonapi_tests.JSONAPIApplicationTests.send

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.openapi = SchemaGenerator().get_schema(public=True)

    def validate_payload(self, payload, schema):
        from jsonschema import Draft4Validator, FormatChecker
        from referencing import Registry, Resource
        full = nullable_schema(self.openapi)
        full['$schema'] = 'http://json-schema.org/draft-04/schema#'
        base = 'urn:shop:openapi'
        registry = Registry().with_resource(base, Resource.from_contents(full))
        # Resolve schema references against the complete OpenAPI document.
        schema = deepcopy(schema)

        def absolute(value):
            if isinstance(value, dict):
                return {key: (base + item if key == '$ref' and item.startswith('#') else absolute(item)) for key, item
                        in value.items()}
            if isinstance(value, list): return [absolute(item) for item in value]
            return value

        validator = Draft4Validator(nullable_schema(absolute(schema)), registry=registry,
                                    format_checker=FormatChecker())
        validator.validate(payload)

    def validate_response(self, path, method, response):
        declared = self.openapi['paths'][path][method]['responses'][str(response.status_code)]
        if response.status_code == 204:
            self.assertFalse(response.content)
            self.assertNotIn('content', declared)
        else:
            self.validate_payload(response.json(), declared['content'][MEDIA]['schema'])

    def test_actual_resource_responses_match_openapi(self):
        owner = self.client_for(self.owner)
        for path in ['/api/v1/products/', '/api/v1/categories/', '/api/v1/carts/', '/api/v1/addresses/',
                     '/api/v1/orders/', '/api/v1/coupons/', '/api/v1/users/', '/api/v1/auth/sessions/']:
            self.validate_response(path, 'get', owner.get(path))
        for resource, obj in [('products', self.product), ('orders', self.order), ('users', self.owner)]:
            self.validate_response(f'/api/v1/{resource}/{{id}}/', 'get', owner.get(f'/api/v1/{resource}/{obj.pk}/'))
        self.validate_response('/api/v1/products/{id}/', 'get',
                               owner.get(f'/api/v1/products/{self.product.pk}/?fields[products]=name'))
        self.validate_response('/api/v1/products/{id}/', 'get',
                               owner.get(f'/api/v1/products/{self.product.pk}/?include=category'))

    def test_actual_mutations_and_action_responses_match_openapi(self):
        admin = self.client_for(self.admin)
        payload = document('products', {'name': 'new', 'size': 'small', 'color': 'red', 'price': '10.00'},
                           {'category': linkage('categories', self.category)})
        declared = self.openapi['paths']['/api/v1/products/']['post']['requestBody']['content'][MEDIA]['schema']
        self.validate_payload(payload, declared)
        response = admin.post('/api/v1/products/', json.dumps(payload), content_type=MEDIA, HTTP_ACCEPT=MEDIA)
        self.assertEqual(response.status_code, 201, response.content)
        self.validate_response('/api/v1/products/', 'post', response)
        client = self.client_for()
        response = self.send(client, 'post', '/api/v1/auth/register/', 'users',
                             {'username': 'newuser', 'password': 'test-password'})
        self.validate_response('/api/v1/auth/register/', 'post', response)
        response = self.send(client, 'post', '/api/v1/auth/login/', 'tokens',
                             {'username': 'newuser', 'password': 'test-password'})
        self.validate_response('/api/v1/auth/login/', 'post', response)
        self.validate_response('/api/v1/auth/refresh/', 'post', client.post('/api/v1/auth/refresh/', HTTP_ACCEPT=MEDIA))
        self.validate_response('/api/v1/products/', 'get',
                               self.client_for().get('/api/v1/products/', HTTP_ACCEPT='application/json'))

    def test_owner_and_admin_order_requests_match_openapi(self):
        declared = self.openapi['paths']['/api/v1/orders/']['post']['requestBody']['content'][MEDIA]['schema']
        owner_payload = document('orders', relationships={'address': linkage('addresses', self.address)})
        admin_payload = document('orders', {'price': '10.00', 'discounted_price': '10.00', 'state': 'pending'},
                                 {'user': linkage('users', self.other),
                                  'address': linkage('addresses', self.other_address)})
        self.validate_payload(owner_payload, declared)
        self.validate_payload(admin_payload, declared)

    def test_missing_route_and_resource_errors_have_consistent_fields(self):
        client = self.client_for()
        for url in ["/api/v1/no-such-route/", "/api/v1/products/999999/"]:
            with self.subTest(url=url):
                response = client.get(url, HTTP_ACCEPT=MEDIA)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response["Content-Type"], MEDIA)
                error = response.json()["errors"][0]
                self.assertEqual(set(error), {"status", "detail", "code"})
                self.assertEqual(error["status"], "404")
                self.assertEqual(error["code"], "not_found")
                self.assertTrue(error["detail"])


class CursorPaginationTests(TestCase):
    setUpTestData = classmethod(jsonapi_tests.JSONAPIApplicationTests.setUpTestData.__func__)
    client_for = jsonapi_tests.JSONAPIApplicationTests.client_for

    def add_products(self, count):
        from products.models import Product
        return [Product.objects.create(
            category=self.category, name=f"extra-{i}", size="small", color="red", price=20,
        ) for i in range(count)]

    def test_next_and_previous_links_traverse_without_duplicates(self):
        from products.models import Product
        self.add_products(24)
        client = self.client_for()
        expected = [str(pk) for pk in Product.objects.order_by("-id").values_list("pk", flat=True)]
        first = client.get("/api/v1/products/?page[size]=10").json()
        self.assertEqual(len(first["data"]), 10)
        self.assertIsNone(first["links"]["prev"])
        self.assertIn("page%5Bcursor%5D", first["links"]["next"])
        second = client.get(first["links"]["next"]).json()
        previous = client.get(second["links"]["prev"]).json()
        self.assertEqual([row["id"] for row in previous["data"]], [row["id"] for row in first["data"]])
        pages = [first]
        while pages[-1]["links"]["next"]:
            pages.append(client.get(pages[-1]["links"]["next"]).json())
            self.assertLessEqual(len(pages), 3)
        actual = [row["id"] for page in pages for row in page["data"]]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertNotIn("count", first["meta"]["pagination"])

    def test_inserts_and_prior_page_deletions_do_not_shift_next_page(self):
        from products.models import Product
        self.add_products(15)
        client = self.client_for()
        expected = [str(pk) for pk in Product.objects.order_by("-id").values_list("pk", flat=True)]
        first = client.get("/api/v1/products/?page[size]=5").json()
        Product.objects.create(category=self.category, name="newer", size="small", color="red", price=20)
        Product.objects.filter(pk=first["data"][0]["id"]).delete()
        seen = [row["id"] for row in first["data"]]
        following = first["links"]["next"]
        while following:
            body = client.get(following).json()
            seen.extend(row["id"] for row in body["data"])
            following = body["links"]["next"]
        self.assertEqual(seen, expected)

    def test_invalid_cursor_page_size_cap_and_no_total_count_query(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from base64 import b64encode
        self.add_products(5)
        client = self.client_for()
        for cursor in ["not-valid-base64", b64encode(b"p=invalid-integer").decode()]:
            response = client.get("/api/v1/products/", {"page[cursor]": cursor})
            self.assertEqual(response.status_code, 404, response.content)
            self.assertIn("detail", response.json()["errors"][0])
        for name in ["page[number]", "page[offset]", "page[after]"]:
            response = client.get("/api/v1/products/", {name: "1"})
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(response.json()["errors"][0]["source"]["parameter"], name)
        with CaptureQueriesContext(connection) as queries:
            response = client.get("/api/v1/products/?page[size]=1000")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["meta"]["pagination"]["page_size"], 100)
        self.assertFalse(any("COUNT(" in query["sql"].upper() for query in queries))
        self.assertEqual(client.get("/api/v1/products/?sort=category&page[size]=1").status_code, 200)

    def test_cursor_pages_preserve_owner_scope_and_address_ordering(self):
        from addresses.models import Address
        for user in (self.owner, self.other):
            for i in range(5):
                Address.objects.create(user=user, country="country", city="city", province="province", zip_code=str(i))
        expected = [str(pk) for pk in
                    Address.objects.filter(user=self.owner).order_by("-id").values_list("pk", flat=True)]
        client = self.client_for(self.owner)
        actual = []
        url = "/api/v1/addresses/?page[size]=2"
        while url:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, response.content)
            body = response.json()
            for row in body["data"]:
                self.assertEqual(row["relationships"]["user"]["data"]["id"], str(self.owner.pk))
                actual.append(row["id"])
            url = body["links"]["next"]
        self.assertEqual(actual, expected)


class DeleteAcknowledgementTests(TestCase):
    setUpTestData = classmethod(jsonapi_tests.JSONAPIApplicationTests.setUpTestData.__func__)
    client_for = jsonapi_tests.JSONAPIApplicationTests.client_for

    def test_every_delete_returns_json_body_and_schema_matches(self):
        from addresses.models import Address
        from carts.models import Carts
        from categories.models import Category
        from coupons.models import Coupon
        from orders.models import Order
        from products.models import Product
        from users.models import User

        schema = SchemaGenerator().get_schema(public=True)
        admin = self.client_for(self.admin)
        for resource, instance in [
            ("addresses", self.address), ("carts", self.cart),
            ("orders", self.order), ("coupons", self.coupon),
            ("products", self.product), ("categories", self.category),
            ("users", self.owner),
        ]:
            with self.subTest(resource=resource):
                response = admin.delete(f"/api/v1/{resource}/{instance.pk}/", HTTP_ACCEPT=MEDIA)
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response["Content-Type"], MEDIA)
                self.assertEqual(response.json(), {"meta": {"message": "Deleted successfully."}})
                declared = schema["paths"][f"/api/v1/{resource}/{{id}}/"]["delete"]["responses"]
                self.assertIn("200", declared)
                self.assertNotIn("204", declared)
                self.assertIn("message",
                              declared["200"]["content"][MEDIA]["schema"]["properties"]["meta"]["properties"])
                if resource == "coupons":
                    self.assertFalse(Coupon.objects.filter(pk=instance.pk).exists())
                else:
                    instance.refresh_from_db()
                    self.assertIsNotNone(instance.deleted_at)
                if resource == "users":
                    self.assertFalse(instance.is_active)


class ParserErrorPointerTests(TestCase):
    setUpTestData = classmethod(jsonapi_tests.JSONAPIApplicationTests.setUpTestData.__func__)
    client_for = jsonapi_tests.JSONAPIApplicationTests.client_for

    def test_parser_errors_point_to_existing_request_locations(self):
        client = self.client_for(self.admin)
        cases = [
            ({"data": {"type": ""}}, "/data/type"),
            ({"data": {}}, "/data"),
            ({}, ""),
            ({"data": {"type": "products", "attributes": []}}, "/data/attributes"),
            ({"data": {"type": "products", "relationships": []}}, "/data/relationships"),
            ({"data": {"type": "products", "id": 1}}, "/data/id"),
            ({"data": {"type": "products", "relationships": {"category": {}}}}, "/data/relationships/category"),
            ({"data": {"type": "products", "relationships": {"category": {"data": {"type": "categories", "id": 1}}}}},
             "/data/relationships/category/data/id"),
            ({"data": {"type": "products", "relationships": {"category": {"data": {"id": "1"}}}}},
             "/data/relationships/category/data"),
            ({"data": {"type": "products", "relationships": {"category": {"data": [{"type": "categories", "id": 1}]}}}},
             "/data/relationships/category/data/0/id"),
            ({"data": {"type": "products", "relationships": {"a/b~c": {"data": {"type": ""}}}}},
             "/data/relationships/a~1b~0c/data/type"),
        ]
        for payload, pointer in cases:
            with self.subTest(pointer=pointer, payload=payload):
                response = client.post("/api/v1/products/", json.dumps(payload), content_type=MEDIA, HTTP_ACCEPT=MEDIA)
                self.assertEqual(response.status_code, 400, response.content)
                error = response.json()["errors"][0]
                self.assertEqual(error["code"], "parse_error")
                self.assertEqual(error["source"]["pointer"], pointer)
                # Pointers for missing fields target the existing parent object.
                value = payload
                for token in pointer.split("/")[1:] if pointer else []:
                    token = token.replace("~1", "/").replace("~0", "~")
                    value = value[int(token)] if isinstance(value, list) else value[token]

    def test_malformed_json_and_resource_conflicts_have_pointers(self):
        client = self.client_for(self.admin)
        response = client.post("/api/v1/products/", "{", content_type=MEDIA, HTTP_ACCEPT=MEDIA)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"][0]["source"]["pointer"], "")
        response = client.post("/api/v1/products/", json.dumps(document("categories", {"name": "shirt"})),
                               content_type=MEDIA, HTTP_ACCEPT=MEDIA)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["errors"][0]["source"]["pointer"], "/data")
