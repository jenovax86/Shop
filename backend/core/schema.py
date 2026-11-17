from copy import deepcopy
from http import HTTPStatus

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_parameter_type, force_instance
from drf_spectacular.utils import OpenApiResponse
from drf_spectacular_jsonapi.schemas.converters import JsonApiRelationshipObject
from drf_spectacular_jsonapi.schemas.openapi import JsonApiAutoSchema
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework_json_api.utils import get_resource_type_from_serializer, is_relationship_field

from users.permissions import IsAdminOrReadOnly

MEDIA_TYPE = "application/vnd.api+json"
ERROR_DOCUMENT = {
    "type": "object",
    "required": ["errors"],
    "properties": {
        "errors": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "code": {"type": "string"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "source": {"type": "object",
                               "properties": {"pointer": {"type": "string"}, "parameter": {"type": "string"}}},
                },
            },
        },
    },
}
LINKS = {"type": "object", "additionalProperties": {"type": "string", "format": "uri", "nullable": True}}


class StringIdRelationship(JsonApiRelationshipObject):
    def patch_id(self):
        super().patch_id()
        self._schema["properties"]["id"] = {"type": "string", "minLength": 1}

    def patch(self):
        super().patch()
        if self.field.allow_null:
            self._schema.pop("nullable", None)
            self._schema["properties"]["data"]["nullable"] = True


class JSONAPIAutoSchema(JsonApiAutoSchema):

    def _map_basic_serializer(self, serializer, direction):
        mapped = AutoSchema._map_basic_serializer(self, serializer, direction)
        if not self.is_json_api_resource_serializer(serializer):
            return mapped
        attributes, relationships = {}, {}
        required_attributes, required_relationships = [], []
        properties = mapped.get("properties", {})
        for name, field in serializer.fields.items():
            schema = properties.get(name)
            if name in ("id", "url") or schema is None:
                continue
            if direction == "request" and field.read_only or direction == "response" and field.write_only:
                continue
            if is_relationship_field(field):
                relationships[name] = StringIdRelationship(field, deepcopy(schema)).__dict__()
                if name in mapped.get("required", []):
                    required_relationships.append(name)
            else:
                attributes[name] = schema
                if name in mapped.get("required", []):
                    required_attributes.append(name)
        resource = {
            "type": "object", "required": ["type"], "additionalProperties": False,
            "properties": {"type": {"type": "string", "enum": [get_resource_type_from_serializer(serializer)]}},
        }
        if direction == "response" or self.method in ("PATCH", "PUT"):
            resource["properties"]["id"] = {"type": "string", "minLength": 1}
            resource["required"].append("id")
        for name, fields, required in [("attributes", attributes, required_attributes),
                                       ("relationships", relationships, required_relationships)]:
            if fields:
                resource["properties"][name] = {"type": "object", "properties": fields}
                if required and direction == "request":
                    resource["properties"][name]["required"] = required
                    resource["required"].append(name)
        if direction == "response":
            resource["properties"]["links"] = deepcopy(LINKS)
        return resource

    def _postprocess_serializer_schema(self, schema, serializer, direction):
        schema = AutoSchema._postprocess_serializer_schema(self, schema, serializer, direction)
        if direction == "request" and getattr(serializer, "component_name",
                                              None) == "OrderCreate" and "oneOf" in schema:
            # Admin payloads also satisfy the owner's smaller input shape.
            schema["anyOf"] = schema.pop("oneOf")
        if direction == "request" and self.is_json_api_resource_serializer(serializer):
            for name in ["type"] + (["id"] if self.method in ("PATCH", "PUT") else []):
                if name not in schema.setdefault("required", []):
                    schema["required"].append(name)
            return {"type": "object", "required": ["data"], "properties": {"data": schema}}
        return schema

    def _get_response_for_code(self, serializer, status_code, media_types=None, direction="response"):
        response = AutoSchema._get_response_for_code(self, serializer, status_code, media_types, direction)
        actual = serializer.response if isinstance(serializer, OpenApiResponse) else serializer
        if self.is_json_api_resource_serializer(actual):
            for content in response.get("content", {}).values():
                if not (self._is_list_view(actual) and self._get_paginator()):
                    content["schema"] = {"type": "object", "required": ["data"],
                                         "properties": {"data": content["schema"], "links": deepcopy(LINKS),
                                                        "meta": {"type": "object"},
                                                        "included": {"type": "array", "items": {"type": "object"}}}}
        if str(status_code) == "201" and self.is_json_api_resource_serializer(actual):
            response.setdefault("headers", {})["Location"] = {"description": "URL of the created resource.",
                                                              "schema": {"type": "string", "format": "uri"}}
        return response

    def get_tags(self):
        tag_names = {
            "addresses": "Addresses",
            "authentication": "Authentication",
            "sessions": "Sessions",
            "carts": "Carts",
            "categories": "Categories",
            "coupons": "Coupons",
            "orders": "Orders",
            "products": "Products",
            "users": "Users",
        }

        tags = super().get_tags()

        return [
            tag_names.get(tag.lower(), tag)
            for tag in tags
        ]

    def get_include_parameter(self):
        if not hasattr(self.view, "get_serializer"):
            return {}
        serializer = self._get_serializer()
        paths = []

        def collect(current, prefix="", seen=()):
            current = force_instance(current)
            if current.__class__ in seen:
                return
            for name, related in getattr(current, "included_serializers", {}).items():
                path = prefix + name
                paths.append(path)
                collect(related, path + ".", seen + (current.__class__,))

        collect(serializer)
        if not paths:
            return {}
        return {("include", "query"): build_parameter_type(
            name="include", location="query", explode=False,
            schema={"type": "array", "items": {"type": "string", "enum": paths}},
            description="Comma-separated related resource paths to include.",
        )}

    def get_sparse_fieldset_parameters(self):
        if not hasattr(self.view, "get_serializer"):
            return {}
        return super().get_sparse_fieldset_parameters()

    def _get_request_body(self, direction="request"):
        body = super()._get_request_body(direction)
        if body is not None:
            body["required"] = True
        return body

    def _get_filter_parameters(self):
        return AutoSchema._get_filter_parameters(self)

    def get_auth(self):
        if self.method in SAFE_METHODS and all(
                isinstance(permission, (AllowAny, IsAdminOrReadOnly)) for permission in self.view.get_permissions()):
            return []
        return super().get_auth()

    def get_operation(self, path, path_regex, path_prefix, method, registry):
        operation = super().get_operation(path, path_regex, path_prefix, method, registry)
        if operation is None:
            return None
        if method == "DELETE":
            operation["responses"].pop("204", None)
            operation["responses"]["200"] = {
                "description": "Deleted successfully.",
                "content": {MEDIA_TYPE: {
                    "schema": {
                        "type": "object", "required": ["meta"],
                        "properties": {"meta": {"type": "object", "required": ["message"],
                                                "properties": {"message": {"type": "string"}}}},
                    },
                    "example": {"meta": {"message": "Deleted successfully."}},
                }},
            }
        codes = [400, 401, 403, 404, 406, 500]
        if method not in SAFE_METHODS:
            codes += [409, 415]
        for code in codes:
            operation["responses"].setdefault(str(code), {"description": HTTPStatus(code).phrase, "content": {
                MEDIA_TYPE: {"schema": deepcopy(ERROR_DOCUMENT)}}})
        return operation
