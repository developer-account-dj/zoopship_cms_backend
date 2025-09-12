# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "superadmin"


class IsSEOFullOnMetaPixel(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "seo"
            and view.basename == "meta-pixel-code"
        )


class IsSEOReadOnlyOnPage(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "seo"
            and view.basename == "page"
            and request.method in SAFE_METHODS
        )