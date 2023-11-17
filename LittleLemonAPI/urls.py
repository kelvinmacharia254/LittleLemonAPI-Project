from django.urls import path

from . import views

urlpatterns = [
    # User management and Authentication urls. Some urls are provided by djoser
    path("users/", views.signup),  # Self registration. Endpoint: /api/users/
    path("users/me", views.user_details),  # get user details. Endpoint: /api/users/me/
    # /auth/token/login  # token generation endpoints
    # user groups managements endpoints.
    path("groups/manager/users", views.managers_details),
    path("groups/manager/users/<int:pk>", views.manager),
    path("groups/delivery-crew/users", views.delivery_crew_details),
    path("groups/delivery-crew/users/<int:pk>", views.delivery_crew),
    # menu items endpoints
    path('menu-items/', views.menu_items),
    path('menu-items/<int:pk>', views.single_menu_item),
    # cart endpoints
    path('cart/menu-items', views.cart),
    # order management endpoints
    path('orders/', views.orders),
]
