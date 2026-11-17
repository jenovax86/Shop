from django.core.exceptions import FieldDoesNotExist, ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class JSONAPIPagination(CursorPagination):
    cursor_query_param = "page[cursor]"
    page_size_query_param = "page[size]"
    page_size = 20
    max_page_size = 100
    ordering = "-pk"

    def paginate_queryset(self, queryset, request, view=None):
        for name in request.query_params:
            if name.startswith("page[") and name not in (self.cursor_query_param, self.page_size_query_param):
                raise ParseError({
                    "detail": "Unsupported pagination parameter. Use page[cursor] and page[size].",
                    "source": {"parameter": name},
                })
        try:
            return super().paginate_queryset(queryset, request, view)
        except (TypeError, ValueError, DjangoValidationError) as exc:
            if request.query_params.get(self.cursor_query_param) is not None:
                raise NotFound(self.invalid_cursor_message) from exc
            raise

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        normalized = []
        for expression in ordering:
            name = expression.lstrip("-")
            if "__" in name:
                raise ValidationError("Cursor pagination cannot sort by nested relationships.")
            try:
                field = queryset.model._meta.pk if name == "pk" else queryset.model._meta.get_field(name)
            except FieldDoesNotExist as exc:
                raise ValidationError("Cursor pagination requires a concrete sorting field.") from exc
            if not field.concrete or field.many_to_many:
                raise ValidationError("Cursor pagination requires a concrete sorting field.")

            normalized.append(("-" if expression.startswith("-") else "") + field.attname)
        return tuple(normalized)

    def get_paginated_response(self, data):
        return Response({
            "results": data,
            "links": {"next": self.get_next_link(), "prev": self.get_previous_link()},
            "meta": {"pagination": {"page_size": self.page_size}},
        })

    def get_paginated_response_schema(self, schema):
        link = {"type": "string", "format": "uri", "nullable": True}
        return {
            "type": "object", "required": ["data", "links", "meta"],
            "properties": {
                "data": schema,
                "links": {"type": "object", "required": ["next", "prev"], "properties": {"next": link, "prev": link}},
                "meta": {"type": "object", "required": ["pagination"], "properties": {
                    "pagination": {"type": "object", "required": ["page_size"], "properties": {
                        "page_size": {"type": "integer", "minimum": 1, "maximum": self.max_page_size},
                    }},
                }},
            },
        }

    def get_schema_operation_parameters(self, view):
        parameters = super().get_schema_operation_parameters(view)
        for parameter in parameters:
            if parameter["name"] == self.cursor_query_param:
                parameter[
                    "description"] = "Opaque cursor from links.next or links.prev. Omit it for the first page; keep the same filters and sort order."
            elif parameter["name"] == self.page_size_query_param:
                parameter["schema"].update(minimum=1, maximum=self.max_page_size, default=self.page_size)
        return parameters
