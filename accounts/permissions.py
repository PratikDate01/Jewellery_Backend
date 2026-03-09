from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    Checks user.role == 'ADMIN' instead of is_staff.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsSupplier(permissions.BasePermission):
    """
    Custom permission to only allow supplier users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'SUPPLIER')

class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customer users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'CUSTOMER')
