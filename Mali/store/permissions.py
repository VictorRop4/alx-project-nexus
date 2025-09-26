
from rest_framework.permissions import BasePermission, SAFE_METHODS


class RolePermission(BasePermission):
    
    """Generic Role-based Permission
        Pass required roles from the view.
    """
    

    def has_permission(self, request, view):
        # Everyone can read
        if request.method in SAFE_METHODS:
            return True

        # Require authentication for write operations
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Admin → can do anything
        if request.user.role == request.user.UserRole.ADMIN:
            return True

        # Check view's defined roles (set on each ViewSet)
        if hasattr(view, "allowed_roles"):
            if request.user.role in view.allowed_roles:
                # For "owner-only" models, verify ownership
                if getattr(view, "owner_field", None):
                    return getattr(obj, view.owner_field) == request.user
                return True  # Non-owner-specific case

        return False
