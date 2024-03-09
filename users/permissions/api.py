from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    allowed = ['update', 'partial_update', 'destroy',
               'blocked', 'change_pswd', 'recommendations',
               'activity', 'actions', 'delete_action']

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if view.action in self.allowed:
            return request.user == obj
        elif view.action == 'follow':
            return request.user != obj
        return True
