from rest_framework.permissions import BasePermission


class IsRoomOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'destroy']:
            return request.user == obj.owner
        return True


class IsPrivateMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'destroy':
            return (
                request.user == obj.first_user or
                request.user == obj.second_user
            )
        return True
