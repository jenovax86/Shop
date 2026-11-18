from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, PolymorphicProxySerializer, \
    extend_schema, extend_schema_view

MEDIA = "application/vnd.api+json"
TOKEN_RESPONSE = {
    "type": "object", "required": ["meta"],
    "properties": {"meta": {"type": "object", "required": ["access"], "properties": {
        "access": {"type": "string", "description": "JWT access token; send it as Authorization: Bearer <token>."}}}},
}
REFRESH_COOKIE = OpenApiParameter(
    "Set-Cookie", OpenApiTypes.STR, OpenApiParameter.HEADER,
    description="Sets the Secure, HttpOnly, SameSite=Lax refresh cookie with expiry matching the JWT. Browser clients must use HTTPS.",
    response=True,
)
LOCATION = OpenApiParameter("Location", OpenApiTypes.URI, OpenApiParameter.HEADER, response=[201])


def action_request(resource_type, attributes, required):
    return {"type": "object", "required": ["data"], "properties": {
        "data": {"type": "object", "required": ["type", "attributes"],
                 "properties": {"type": {"type": "string", "enum": [resource_type]},
                                "attributes": {"type": "object", "required": required, "properties": attributes}}}}}


def credentials(resource_type, registration=False):
    username = {"type": "string"}
    password = {"type": "string", "format": "password", "writeOnly": True}
    if registration:
        username["maxLength"] = 20
        password.update(minLength=6, maxLength=100)
    return action_request(resource_type, {"username": username, "password": password}, ["username", "password"])


class RegistrationDocumentation(OpenApiViewExtension):
    target_class = "auth.views.RegisterAPIView"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        response = {"type": "object", "required": ["data", "meta"], "properties": {
            "data": {"type": "object", "required": ["type", "id", "attributes"],
                     "properties": {"type": {"type": "string", "enum": ["users"]}, "id": {"type": "string"},
                                    "attributes": {"type": "object", "required": ["username"],
                                                   "properties": {"username": {"type": "string"}}},
                                    "links": {"type": "object",
                                              "properties": {"self": {"type": "string", "format": "uri"}}}}},
            "meta": TOKEN_RESPONSE["properties"]["meta"],
        }}
        return extend_schema_view(post=extend_schema(
            tags=["Authentication"], summary="Register a user",
            description="Public endpoint. Creates the account and login session atomically. Returns the new user and meta.access, and sets the HTTP-only refresh cookie.",
            request={MEDIA: credentials("users", registration=True)}, responses={201: response},
            parameters=[REFRESH_COOKIE, LOCATION],
            examples=[OpenApiExample("Registration", value={
                "data": {"type": "users", "attributes": {"username": "alice", "password": "example-password"}}},
                                     request_only=True)],
        ))(Documented)


class LoginDocumentation(OpenApiViewExtension):
    target_class = "auth.views.LoginAPIView"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(post=extend_schema(
            tags=["Authentication"], summary="Log in and create a session",
            description="Public endpoint. Read the access token from meta.access. The refresh token is delivered only through the HTTP-only cookie. Use Swagger's Authorize button with the access token to call protected endpoints.",
            request={MEDIA: credentials("tokens")}, responses={200: TOKEN_RESPONSE}, parameters=[REFRESH_COOKIE],
            examples=[OpenApiExample("Login", value={
                "data": {"type": "tokens", "attributes": {"username": "alice", "password": "example-password"}}},
                                     request_only=True)],
        ))(Documented)


class RefreshDocumentation(OpenApiViewExtension):
    target_class = "auth.views.RefreshAPIView"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(post=extend_schema(
            tags=["Authentication"], summary="Refresh the access token",
            description="No request body. Requires the refresh cookie set by login. Validates the current session and rotates the refresh token. Browsers send the HTTP-only cookie automatically on same-origin HTTPS requests; do not paste the refresh token into a Bearer header.",
            auth=[{"refreshCookie": []}], request=None, responses={200: TOKEN_RESPONSE}, parameters=[REFRESH_COOKIE],
        ))(Documented)


class GoogleLoginDocumentation(OpenApiViewExtension):
    target_class = "auth.views.GoogleLogin"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(get=extend_schema(
            tags=["Authentication"], summary="Start Google login",
            description="Open this URL in a browser to begin Google authorization. Redirects to Google and stores OAuth state in the Django session. Swagger's fetch-based Try it out cannot complete the browser redirect flow.",
            request=None, responses={302: OpenApiResponse(description="Redirect to Google's authorization endpoint.")},
            parameters=[OpenApiParameter("Location", OpenApiTypes.URI, OpenApiParameter.HEADER, response=[302])],
        ))(Documented)


class GoogleCallbackDocumentation(OpenApiViewExtension):
    target_class = "auth.views.GoogleCallback"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(get=extend_schema(
            tags=["Authentication"], summary="Complete Google login",
            description="Google redirect callback; not a manual login endpoint. Requires matching OAuth state and the browser's Django session cookie. Returns meta.access and sets the refresh cookie.",
            request=None, responses={200: TOKEN_RESPONSE}, parameters=[
                OpenApiParameter("code", OpenApiTypes.STR, description="Google authorization code."),
                OpenApiParameter("state", OpenApiTypes.STR, description="OAuth state matching the Django session."),
                OpenApiParameter("error", OpenApiTypes.STR, description="Google error on rejected authorization."),
                REFRESH_COOKIE,
            ],
        ))(Documented)


class AddressDocumentation(OpenApiViewExtension):
    target_class = "addresses.views.AddressViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(
            list=extend_schema(
                tags=["Addresses"],
                summary="Get addresses",
                description="Retrieve a list of addresses."
            ),

            create=extend_schema(
                tags=["Addresses"],
                summary="Create address",
                description="Create a new address."
            ),

            retrieve=extend_schema(
                tags=["Addresses"],
                summary="Get single address",
                description="Retrieve details of a specific address."
            ),

            update=extend_schema(
                tags=["Addresses"],
                summary="Update address",
                description="Replace an existing address using PUT."
            ),

            partial_update=extend_schema(
                tags=["Addresses"],
                summary="Partially update address",
                description="Update specific fields of an existing address using PATCH."
            ),

            destroy=extend_schema(
                tags=["Addresses"],
                summary="Delete address",
                description="Delete an existing address."
            ),

        )(Documented)

class CartDocumentation(OpenApiViewExtension):
    target_class = "carts.views.CartsViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(
            list=extend_schema(
                tags=["Carts"],
                summary="Get carts",
                description="Retrieve a list of carts."
            ),

            create=extend_schema(
                tags=["Carts"],
                summary="Create cart",
                description="Create a new cart."
            ),

            retrieve=extend_schema(
                tags=["Carts"],
                summary="Get single cart",
                description="Retrieve details of a specific cart."
            ),

            update=extend_schema(
                tags=["Carts"],
                summary="Update cart",
                description="Replace an existing cart using PUT."
            ),

            partial_update=extend_schema(
                tags=["Carts"],
                summary="Partially update cart",
                description="Update specific fields of an existing cart using PATCH."
            ),

            destroy=extend_schema(
                tags=["Carts"],
                summary="Delete cart",
                description="Delete an existing cart."
            ),
        )(Documented)


class ProductMediaDocumentation(OpenApiViewExtension):
    target_class = "products.views.ProductMediaViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(
            list=extend_schema(
                tags=["Product Media"],
                summary="Get Product Media",
                description="Retrieve a list of product media."
            ),

            create=extend_schema(
                tags=["Product Media"],
                summary="Upload Product Media",
                description="Upload one or more images for a product."
            ),

            retrieve=extend_schema(
                tags=["Product Media"],
                summary="Get Product Media Details",
                description="Retrieve details of a specific product media."
            ),

            update=extend_schema(
                tags=["Product Media"],
                summary="Update Product Media",
                description="Replace an existing product media using PUT."
            ),

            partial_update=extend_schema(
                tags=["Product Media"],
                summary="Partially Update Product Media",
                description="Update specific fields of an existing product media using PATCH."
            ),

            destroy=extend_schema(
                tags=["Product Media"],
                summary="Delete Product Media",
                description="Delete an existing product media."
            ),
        )(Documented)


class SessionDocumentation(OpenApiViewExtension):
    target_class = "sessions.views.SessionViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        revoke = action_request("session-revocations", {"session_ids": {"type": "array", "minItems": 1, "maxItems": 100,
                                                                        "items": {"type": "integer", "minimum": 1}}},
                                ["session_ids"])
        response = {"type": "object", "required": ["meta"], "properties": {
            "meta": {"type": "object", "required": ["revoked_sessions"],
                     "properties": {"revoked_sessions": {"type": "integer", "minimum": 0}}}}}
        return extend_schema_view(
            list=extend_schema(tags=["Sessions"], summary="Get Sessions",
                               description="Users see their own active sessions; administrators see all sessions."),
            revoke=extend_schema(tags=["Sessions"], summary="Revoke sessions",
                                 description="Users can revoke only their own sessions. Administrators can revoke sessions across accounts. Revocation prevents refresh; existing access tokens expire normally.",
                                 request={MEDIA: revoke}, responses={200: response}, filters=False, examples=[
                    OpenApiExample("Revoke sessions", value={
                        "data": {"type": "session-revocations", "attributes": {"session_ids": [1, 2]}}},
                                   request_only=True)]),
            logout=extend_schema(tags=["Sessions"], summary="Log out the current session",
                                 description="Requires the Bearer access token. Revokes its session and expires the refresh cookie. Returns an empty body.",
                                 request=None, responses={204: None}, filters=False, parameters=[REFRESH_COOKIE]),
        )(Documented)


class ProductDocumentation(OpenApiViewExtension):
    target_class = "products.views.ProductViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(
            list=extend_schema(
                tags=["Products"],
                summary="Get products",
                description="Retrieve a list of products."
            ),

            create=extend_schema(
                tags=["Products"],
                summary="Create product",
                description="Create a new product."
            ),

            retrieve=extend_schema(
                tags=["Products"],
                summary="Get single product",
                description="Retrieve details of a specific product."
            ),

            update=extend_schema(
                tags=["Products"],
                summary="Update product",
                description="Replace an existing product using PUT."
            ),

            partial_update=extend_schema(
                tags=["Products"],
                summary="Partially update product",
                description="Update specific fields of an existing product using PATCH."
            ),

            destroy=extend_schema(
                tags=["Products"],
                summary="Delete product",
                description="Delete an existing product."
            ),
        )(Documented)


class UserDocumentation(OpenApiViewExtension):
    target_class = "users.views.UserViewSet"

    def view_replacement(self):
        class Documented(self.target_class):
            pass

        return extend_schema_view(
            list=extend_schema(
                tags=["Users"],
                summary="Get users",
                description="Retrieve a list of users."
            ),

            create=extend_schema(
                tags=["Users"],
                summary="Create user",
                description="Create a new user."
            ),

            retrieve=extend_schema(
                tags=["Users"],
                summary="Get single user",
                description="Retrieve details of a specific user."
            ),

            update=extend_schema(
                tags=["Users"],
                summary="Update user",
                description="Replace an existing user's information using PUT."
            ),

            partial_update=extend_schema(
                tags=["Users"],
                summary="Partially update user",
                description="Update specific fields of an existing user using PATCH."
            ),

            destroy=extend_schema(
                tags=["Users"],
                summary="Delete user",
                description="Delete an existing user."
            ),
        )(Documented)


class OrderDocumentation(OpenApiViewExtension):
    target_class = "orders.views.OrderViewSet"

    def view_replacement(self):
        from orders.serializers import AdminOrderSerializer, OrderSerializer

        class Documented(self.target_class):
            pass

        return extend_schema_view(create=extend_schema(
            description="Regular users create an order from their own cart with their own address and optional coupon. Pricing and initial state are calculated by the server. Administrators can instead supply user, price, discounted_price and state to create an order directly. Choose the matching request variant.",
            request=PolymorphicProxySerializer(
                component_name="OrderCreate",
                serializers=[OrderSerializer, AdminOrderSerializer],
                resource_type_field_name=None,
            ),
        ))(Documented)
