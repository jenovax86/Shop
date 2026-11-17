# JSON:API interface

The API uses JSON:API documents with the `application/vnd.api+json` media type. Endpoint URLs and the owner/admin
permission rules stay the same. This changes the request and response format used by existing clients; the former
`success`, `data`, `errors`, and `status_code` envelope is no longer used.

## Headers

Send these headers for resource requests:

```http
Accept: application/vnd.api+json
Content-Type: application/vnd.api+json
Authorization: Bearer ACCESS_TOKEN
```

The authorization header is not needed for product/category reads or the public authentication endpoints. The
content-type header is needed when sending a JSON:API body. Plain `application/json` request bodies are rejected with
415. An incompatible `Accept` header produces 406. Unknown JSON:API extensions are not supported; unknown profiles are
ignored.

## Resources and relationships

Resource types are `users`, `addresses`, `carts`, `categories`, `products`, `orders`, `order-products`, `coupons`, and
`sessions`. Resource IDs are strings.

For example, create a product as an administrator:

```http
POST /api/v1/products/
```

```json
{
  "data": {
    "type": "products",
    "attributes": {
      "name": "T-shirt",
      "gender": "male",
      "size": "small",
      "color": "red",
      "price": "25.00"
    },
    "relationships": {
      "category": {
        "data": {
          "type": "categories",
          "id": "1"
        }
      }
    }
  }
}
```

A resource response has this form:

```json
{
  "data": {
    "type": "products",
    "id": "12",
    "attributes": {
      "name": "T-shirt",
      "gender": "male",
      "size": "small",
      "color": "red",
      "price": "25.00"
    },
    "relationships": {
      "category": {
        "data": {
          "type": "categories",
          "id": "1"
        }
      }
    },
    "links": {
      "self": "https://api.example.com/api/v1/products/12/"
    }
  }
}
```

POST creates a resource without a client-supplied ID. Client-generated IDs are not supported and return 403. PATCH and
PUT must include the matching string ID and type. For example:

```http
PATCH /api/v1/products/12/
```

```json
{
  "data": {
    "type": "products",
    "id": "12",
    "attributes": {
      "price": "30.00"
    }
  }
}
```

A mismatching type or URL/body ID returns 409. Successful resource deletion returns 200 with
`{"meta": {"message": "Deleted successfully."}}`.

Owner relationships use `user` in addresses, carts, orders, coupons, and sessions. Address input therefore uses a `user`
relationship instead of the former scalar `user_id`. Ordinary users cannot reassign ownership; administrators can. An
order's `address` and `coupon` are relationships. Reference coupons by their resource ID, not by their code. Coupon
codes remain readable attributes.

## Lists, filtering and includes

Lists use cursor pagination and return a `data` array, `links.next`, `links.prev`, and `meta.pagination.page_size`.
Total counts and numbered pages are not returned. General page size is 20; products and addresses default to 10. Clients
may request up to 100 resources per page.

Examples:

```text
GET /api/v1/products/?page[size]=10
GET /api/v1/products/?page[cursor]=OPAQUE_CURSOR&page[size]=10
GET /api/v1/products/?filter[min_price]=10&filter[max_price]=50
GET /api/v1/products/?filter[category]=1&sort=-price
GET /api/v1/products/?include=category
GET /api/v1/products/?fields[products]=name,price,category
GET /api/v1/carts/?include=product.category
GET /api/v1/orders/12/?include=items.product.category
```

Product filter fields remain the fields declared in `products/filters.py`, now using `filter[...]` parameter names.
Sorting uses `sort`; pagination uses `page[cursor]` and `page[size]`. Follow `links.next` or `links.prev` unchanged to
move between pages; omit the cursor for the first page. Keep the same filters and sort order when following a cursor.
The default order is newest ID first; products and addresses retain their own default page sizes. Legacy `page[number]`
and other unsupported pagination parameters return 400. Cursors work best with immutable ordering fields such as IDs.
Sorting by mutable fields can change traversal if those values are edited between requests. Unsupported query
parameters, fields for sorting/filtering, or includes return 400. Sparse fieldsets use serializer field names, including
existing underscores. Related resources requested through supported `include` paths appear in the top-level `included`
array.

Supported include paths start with `category` for products, `product` for carts, and `items` for orders. Nested paths
follow those serializers. User/profile relationships are not includable.

Collection-level bulk PATCH/DELETE is no longer supported. Use individual resource endpoints; the JSON:API Atomic
Operations extension has not been implemented.

## Registration, login and refresh

Registration accepts `data.type = "users"` with `username` and `password` attributes. It returns 201 with the new user
in `data`, an access token in `meta.access`, and an HTTP-only refresh cookie.

Login:

```http
POST /api/v1/auth/login/
```

```json
{
  "data": {
    "type": "tokens",
    "attributes": {
      "username": "alice",
      "password": "example-password"
    }
  }
}
```

Successful login, refresh, and Google callback return:

```json
{
  "meta": {
    "access": "ACCESS_TOKEN"
  }
}
```

The refresh JWT remains in the HTTP-only, Secure, SameSite=Lax `refresh` cookie. Its cookie expiry matches the token
expiry. Send the cookie to `POST /api/v1/auth/refresh/`; no request body is required. Refresh rotates the cookie and
invalidates the old refresh token through the session table. Browser clients must use HTTPS and include credentials when
appropriate.

The Google redirect/callback flow and OAuth state validation stay managed by Authlib.

## Session actions

List sessions using `GET /api/v1/auth/sessions/`. To revoke sessions:

```http
POST /api/v1/auth/sessions/revoke/
```

```json
{
  "data": {
    "type": "session-revocations",
    "attributes": {
      "session_ids": [
        1,
        2
      ]
    }
  }
}
```

The response is `{"meta": {"revoked_sessions": 2}}`. Users can revoke only their own sessions; administrators can revoke
sessions across accounts. `POST /api/v1/auth/sessions/logout/` returns 204 and clears the refresh cookie. Session
revocation prevents refresh; existing access tokens remain valid until expiry unless the account is disabled.

## Errors

Errors use an `errors` array without primary `data`:

```json
{
  "errors": [
    {
      "status": "400",
      "code": "invalid",
      "detail": "Price must be greater than zero.",
      "source": {
        "pointer": "/data/attributes/price"
      }
    }
  ]
}
```

Authentication errors, permission errors, validation errors, conflicts, and unknown API URLs use this document format.
Error members vary according to the failure. OPTIONS metadata and operation results use top-level `meta`.

## Dependencies and checks

Run `poetry install` to install the locked JSON:API dependency. No database schema changes or migrations were introduced
by this conversion. Regression tests live in `users/tests.py` and cover JSON:API documents and the existing permission
boundaries. Use the project's usual Django test-database configuration when running
`poetry run python manage.py test users`.

## Interactive API documentation

Swagger UI is available at `/api/docs/`, with the OpenAPI JSON schema at `/api/schema/`. See [OPENAPI.md](OPENAPI.md)for
authentication, browser-cookie handling and schema export instructions.
