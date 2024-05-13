from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in [
            'retrieve',
            'add_like',
            'add_comment',
            'delete_comment',
        ]:
            return True
        if view.action in ['destroy', 'partial_update']:
            return request.user == obj.owner
        return True
