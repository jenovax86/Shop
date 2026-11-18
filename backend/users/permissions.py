from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin(user):
    return bool(user and user.is_authenticated and (user.role == "admin" or user.is_superuser))


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request.user)


class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "cart_id"):
            return obj.cart.user_id == request.user.pk

        return is_admin(request.user) or obj.user_id == request.user.pk


class IsAdminOrSelf(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return view.action != "create" or is_admin(user)

    def has_object_permission(self, request, view, obj):
        return is_admin(request.user) or obj.pk == request.user.pk
