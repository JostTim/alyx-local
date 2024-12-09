from rest_framework.permissions import BasePermission, IsAuthenticated


class BaseRestPublicPermission(BasePermission):
    """
    The purpose is to prevent public users from interfering in any way using writable methods
    """

    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        elif request.user.is_public_user:
            return False
        else:
            return True


def rest_permission_classes():
    permission_classes = (IsAuthenticated & BaseRestPublicPermission,)
    return permission_classes
