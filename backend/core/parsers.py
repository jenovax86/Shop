from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.parsers import JSONParser


class JSONAPIParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except ParseError as exc:
            self.add_pointer(exc, "")
            raise

    def parse_data(self, result, parser_context):
        resource = result.get("data") if isinstance(result, dict) else None
        if isinstance(resource, dict):
            self.validate_identifier(resource, require_id=False, pointer="/data")
            request = (parser_context or {}).get("request")
            if request is not None and request.method == "POST" and "id" in resource:
                raise PermissionDenied({
                    "detail": "Client-generated resource IDs are not supported.",
                    "source": {"pointer": "/data/id"},
                })
            attributes = resource.get("attributes", {})
            relationships = resource.get("relationships", {})
            if not isinstance(attributes, dict):
                self.parse_error("Attributes must be an object.", "/data/attributes")
            if not isinstance(relationships, dict):
                self.parse_error("Relationships must be an object.", "/data/relationships")
            for container, fields in [("attributes", attributes), ("relationships", relationships)]:
                for name in ("id", "type"):
                    if name in fields:
                        self.parse_error(
                            "The id and type members must not be attributes or relationships.",
                            f"/data/{container}/{name}",
                        )
            for name in attributes:
                if name in relationships:
                    self.parse_error(
                        "Attributes and relationships must not share a name.",
                        "/data/relationships/" + self.escape_token(name),
                    )
            for name, relationship in relationships.items():
                pointer = "/data/relationships/" + self.escape_token(name)
                if not isinstance(relationship, dict) or "data" not in relationship:
                    self.parse_error("Writable relationships must contain resource linkage in data.", pointer)
                linkage = relationship["data"]
                if linkage is None:
                    continue
                if isinstance(linkage, list):
                    for index, identifier in enumerate(linkage):
                        self.validate_identifier(identifier, pointer=f"{pointer}/data/{index}")
                else:
                    self.validate_identifier(linkage, pointer=pointer + "/data")
        try:
            return super().parse_data(result, parser_context)
        except (ParseError, Conflict) as exc:
            pointer = "/data" if isinstance(result, dict) and "data" in result else ""
            self.add_pointer(exc, pointer)
            raise

    @staticmethod
    def escape_token(value):
        return value.replace("~", "~0").replace("/", "~1")

    @staticmethod
    def parse_error(detail, pointer):
        raise ParseError({"detail": detail, "source": {"pointer": pointer}})

    @staticmethod
    def add_pointer(exc, pointer):
        if isinstance(exc.detail, dict):
            exc.detail.setdefault("source", {}).setdefault("pointer", pointer)
        else:
            exc.detail = {"detail": exc.detail, "source": {"pointer": pointer}}

    @classmethod
    def validate_identifier(cls, value, require_id=True, pointer="/data"):
        if not isinstance(value, dict) or not isinstance(value.get("type"), str) or not value["type"]:
            location = pointer + "/type" if isinstance(value, dict) and "type" in value else pointer
            cls.parse_error("Resource type must be a non-empty string.", location)
        if (require_id or "id" in value) and (not isinstance(value.get("id"), str) or not value["id"]):
            location = pointer + "/id" if "id" in value else pointer
            cls.parse_error("Resource id must be a non-empty string.", location)
