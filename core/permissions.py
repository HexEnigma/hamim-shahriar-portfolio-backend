from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_owner(user):
    return bool(user and user.is_authenticated and user.is_superuser)


class IsOwnerOrReadOnly(BasePermission):
    """Anyone may read; only the authenticated superuser may write."""
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_owner(request.user)


class IsOwner(BasePermission):
    """Owner only, for reads as well (private data)."""
    def has_permission(self, request, view):
        return is_owner(request.user)