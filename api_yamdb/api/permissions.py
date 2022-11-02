from rest_framework.permissions import permissions

from reviews.models import User

class ReadOnlyPermission(BasePermission):
    """Класс для разрешения доступа только для чтения."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class UserIsAuthor(BasePermission):

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)

class AdminPermission(BasePermission):
    """Класс для разрешения доступа только администратору."""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return (
                request.user.role == User.ADMIN
                or request.user.is_staff
                or request.user.is_superuser
            )

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or (
            request.user.role == User.ADMIN
            or request.user.is_staff
            or request.user.is_superuser
        )
