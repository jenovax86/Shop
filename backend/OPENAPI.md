# OpenAPI and Swagger UI

The backend provides:

- **Swagger UI:** `/api/docs/`
- **OpenAPI JSON schema:** `/api/schema/`

Both documentation endpoints are publicly readable. They describe the API and contain no account records or live tokens.
API authorization rules still apply when executing requests from Swagger.

## Run locally

Install the locked dependencies and start the Django development server as usual:

```sh
poetry install
poetry run python manage.py runserver
```

For the default development address, open `http://127.0.0.1:8000/api/docs/`. The development server serves Swagger's
JavaScript and CSS from the installed `drf-spectacular-sidecar` package, without a CDN. Production deployments must run
`collectstatic` and serve the configured static directory through their usual web server/storage setup.

## Try authenticated requests

1. Use **Authentication → Register a user** or **Log in and create a session**.
2. Send the JSON:API body shown in the example. Login expects `data.type: "tokens"`; registration expects
   `data.type: "users"`.
3. Copy the access token from `meta.access`.
4. Click **Authorize** and paste the access token itself. Swagger adds the `Bearer` prefix.
5. Execute a protected request.

The refresh token remains in an HTTP-only, Secure cookie. Swagger is configured to include browser credentials. Login
and refresh should run on the same HTTPS origin for browser cookie handling. The refresh operation has no request body;
its cookie security scheme documents the cookie, rather than requiring a refresh token in the Authorization header.
Logout uses the Bearer token and returns 204.

Google login is a browser redirect flow. Open `/api/v1/auth/google/login/` in a browser; Swagger's fetch-based Try it
out cannot complete Google's redirect and consent flow. The callback requires the matching OAuth state and Django
session cookie.

## JSON:API and roles

The schema documents `application/vnd.api+json`, string resource IDs, attributes, relationships, cursor pagination (
`page[cursor]` and `page[size]` with next/previous links), `filter[...]`, sorting, sparse fieldsets and supported nested
includes. It also documents JSON:API error objects and JSON acknowledgements for deletion and the empty response used
for logout.

Product/category reads have no security requirement. Writes require an administrator. Personal-resource endpoints
require Bearer authentication and enforce ownership at runtime. Administrators can manage records across accounts.

Role-dependent schemas include administrative fields so they are discoverable in the documentation. Their presence in
Swagger does not grant a regular user permission to modify them. Order creation offers owner and administrator request
variants: owners supply their address and optional coupon and receive server-calculated pricing; administrators may
supply ownership, prices and state directly.

## Export and validate

```sh
poetry run python manage.py spectacular --file openapi.yaml --validate --fail-on-warn
```

This exports the schema without querying the database. OpenAPI annotations for custom authentication/session operations
live in `core/api_docs.py`; the JSON:API schema adapter is in `core/schema.py`. Resource schemas are generated from the
serializers. Runtime request and response formats are documented in `JSON_API.md`.

Tests in `core/tests.py` validate the schema, check Swagger's local assets and security requirements, and compare actual
API payloads against the documented shapes. The existing JSON:API/permission tests remain in `users/tests.py`.
