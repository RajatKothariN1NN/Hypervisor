from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists()

class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Developer').exists()

class IsViewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Developer').exists() or request.user.groups.filter(name='Viewer').exists()

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return IsViewer().has_permission(request, view)
        return IsAdmin().has_permission(request, view)