from django.urls import path

from . import views

urlpatterns = [
    # User management and Authentication urls
    path("users/", views.signup),  # Self registration. Endpoint: /api/users/
    path("users/me", views.get_user_details),  # get user details. Endpoint: /api/users/me/

    path('menu-items/', views.menu_items),
    path('menu-items/<int:pk>', views.single_menu_item),
]
