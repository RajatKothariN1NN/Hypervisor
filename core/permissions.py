from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists()  # "Admin", not "ADMIN"

class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Developer').exists()

class IsViewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Developer').exists() or request.user.groups.filter(name='Viewer').exists()