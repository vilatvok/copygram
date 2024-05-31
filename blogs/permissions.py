from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ['destroy', 'update', 'partial_update', 'archive']:
            return request.user == obj.owner
        return True
