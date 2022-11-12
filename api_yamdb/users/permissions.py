from rest_framework.permissions import BasePermission

### Мы его во users/views.py используем)
class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == 'admin'
        )
