# permissions.py
from rest_framework import permissions


class IsManager(permissions.BasePermission):
    allowed_group = 'Manager'  # Replace with the name of your allowed group

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False  # Deny access if the user is not authenticated

        # Check if the user belongs to the allowed group
        return request.user.groups.filter(name=self.allowed_group).exists()
        # By Django default, the admin use has all permissions regardless of group membership or not.
        # Implement return statement as below to restrict admin user
        # return (
        #     not request.user.is_superuser and
        #     request.user.groups.filter(name=self.allowed_group).exists()
        # )


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False  # Deny access if the user is not authenticated

        # Check if the user belongs to any group
        return not request.user.groups.exists()  # Deny access if the user belongs to any group
