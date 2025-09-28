
from rest_framework.permissions import BasePermission, SAFE_METHODS


class RolePermission(BasePermission):
    """
    Generic Role-based Permission.
    - Everyone can read (safe methods).
    - Write requires authentication *and* the user must be in allowed_roles
      or an admin.
    - Optionally checks object ownership if `owner_field` is defined on the view.
    """

    def has_permission(self, request, view):
        # Everyone can read
        if request.method in SAFE_METHODS:
            return True

        # Must be logged in
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can do anything
        if request.user.role == request.user.UserRole.ADMIN:
            return True

        # For non-admins: view must declare allowed_roles
        if hasattr(view, "allowed_roles"):
            return request.user.role in view.allowed_roles

        # If no allowed_roles are defined, deny by default
        return False

    def has_object_permission(self, request, view, obj):
        # Safe methods are always allowed
        if request.method in SAFE_METHODS:
            return True

        # Admins can do anything
        if request.user.role == request.user.UserRole.ADMIN:
            return True

        # Check allowed_roles
        if hasattr(view, "allowed_roles") and request.user.role in view.allowed_roles:
            # If the view enforces ownership, check it
            if getattr(view, "owner_field", None):
                return getattr(obj, view.owner_field) == request.user
            return True

        return False
