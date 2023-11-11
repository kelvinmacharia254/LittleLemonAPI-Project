from django.urls import path

from . import views

urlpatterns = [
    # User management and Authentication urls. Some urls are provided by djoser
    path("users/", views.signup),  # Self registration. Endpoint: /api/users/
    path("users/me", views.get_user_details),  # get user details. Endpoint: /api/users/me/
    # /auth/token/login  # token generation endpoints
    # user groups managements endpoints.
    path("groups/manager/users", views.get_managers_details),
    # menu items endpoints
    path('menu-items/', views.menu_items),
    path('menu-items/<int:pk>', views.single_menu_item),
]
