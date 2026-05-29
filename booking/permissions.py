from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff or
            request.user.groups.filter(name='Менеджер заявок').exists()
        )


class IsAdminOrManagerOrReadOwn(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if request.user.groups.filter(name='Менеджер заявок').exists():
            return request.method in SAFE_METHODS or True
        return obj.user == request.user