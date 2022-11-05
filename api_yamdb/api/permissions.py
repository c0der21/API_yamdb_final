from rest_framework.permissions import SAFE_METHODS, BasePermission

from reviews.models import ADMIN, MODERATOR


class ReadOnlyPermission(BasePermission):
    """Класс для разрешения доступа только для чтения."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class ObjectAuthorPermission(BasePermission):
    """Класс для разрешения доступа только для чтения или автору."""

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user == obj.author


class AdminPermission(BasePermission):
    """Класс для разрешения доступа только администратору."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == ADMIN
        )


class IsAdminUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.role == ADMIN
        return False

class AdminModeratorAuthorPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.role == MODERATOR
            or request.user.role == ADMIN
        )
