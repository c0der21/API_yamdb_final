from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == 'admin'
        )

class ModeratorPermission(BasePermission):
    """Класс для разрешения доступа только модератору."""

class IsAdminUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or (request.user.is_authenticated and (
                    request.user.role == 'admin' or request.user.is_superuser)))

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.role == 'admin' or request.user.is_superuser)


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user)


class IsModeratorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.role == 'moderator')
    
