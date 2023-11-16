# Create your views here.
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import IsAuthenticated, IsAdminUser

# import models
from .models import (
    MenuItem,
    Category,
    Cart,
)

from .serializers import (
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
)

from django.contrib.auth.models import User, Group


# User management and Authentication Endpoints.
@api_view(['POST'])
def signup(request):
    """
    Allows new user to register themselves
    :param request:
    :return: user details or error if any
    """
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_details(request):
    """
    Fetch details of the authenticated user
    :param request:
    :return: user details
    """
    user = request.user

    # option without using the serializer
    # return Response({
    #     'username': user.username,
    #     'email': user.email,
    # })
    # option 2
    user_details_serialized = UserSerializer(user)

    return Response(user_details_serialized.data, status.HTTP_200_OK)


# User groups management endpoints
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def managers_details(request):
    """
    Endpoint: /api/groups/manager/users
    GET: List all Manager
    POST: Adds user to the manager group/promote user to a manager
    :param request:
    :return: JSON() and status code
    """
    if request.method == 'GET':
        # Get the 'Manager' group or raise a 404 if it doesn't exist
        manager_group = get_object_or_404(Group, name='Manager')
        # Get users in the 'Manager' group
        manager_users = User.objects.filter(groups=manager_group)  # or manager_users = manager_group.user_set.all()
        manager_users_serialized = UserSerializer(manager_users, many=True)
        return Response(manager_users_serialized.data, status.HTTP_200_OK)

    if request.method == 'POST':
        # Get the user instance
        username = request.data['username']  # get username from POST request
        # user = get_object_or_404(User, username=username)
        try:
            user = get_object_or_404(User, username=username)
        except Http404:
            return Response({"message": f"User with username '{username}' not found."}, status.HTTP_404_NOT_FOUND)

        # Get the 'Manager' group
        manager_group = Group.objects.get(name='Manager')
        if user.groups.filter(name=manager_group).exists():  # inform if the user is already a manager
            return Response({"message": f"The user <{user}> is already a manager."}, status.HTTP_204_NO_CONTENT)
        else:  # Add user to Manager
            user.groups.add(manager_group)
            return Response({"message": f"You promoted {user} to a manager."}, status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def manager(request, pk):  # Endpoint/groups/manager/users/<int:pk>
    """
    Demote user from manager group via DELETE Request
    :param request:
    :param pk:
    :return:
    """
    if request.method == 'DELETE':
        manager_group = get_object_or_404(Group, name='Manager')
        user = get_object_or_404(User, id=pk)
        if user.groups.filter(name=manager_group).exists():  # if a manager, remove/demote user
            user.groups.remove(manager_group)
            return Response({"message": f"<{user.username}> is demoted. No longer manager."}, status.HTTP_200)
        # inform if user is not a manager
        return Response({"message": f"<{user.username}> is not a manager."}, status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def delivery_crew_details(request):
    """
    Endpoint: /api/groups/delivery-crew/users
    GET: List all Delivery crew group users
    POST: Adds user to the delivery group/promote user to a delivery crew.
    :param request:
    :return: JSON() and status code

    e.g : POST data
        {
            "username":"username"
        }
    """
    delivery_crew_group = get_object_or_404(Group, name='Delivery crew')
    if request.method == 'GET':
        delivery_crew_users = User.objects.filter(groups=delivery_crew_group)
        delivery_crew_user_serialized = UserSerializer(delivery_crew_users, many=True)
        return Response(delivery_crew_user_serialized.data, status.HTTP_200_OK)
    if request.method == 'POST':
        # Get the user instance from POST request
        username = request.data['username']
        try:
            user = get_object_or_404(User, username=username)
        except Http404:
            return Response({"message": f"User with username '{username}' not found."}, status.HTTP_404_NOT_FOUND)

        if user.groups.filter(name=delivery_crew_group).exists():  # inform if the user is already a delivery crew
            return Response({"message": f"The user <{user}> is already a delivery crew."}, status.HTTP_204_NO_CONTENT)
        else:  # Add user to Manager
            user.groups.add(delivery_crew_group)
            return Response({"message": f"You promoted <{user}> to a delivery crew."}, status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delivery_crew(request, pk):  # Endpoint/groups/delivery-crew/users/<int:pk>
    """
    Demote user from delivery crew group via DELETE Request
    :param request:
    :param pk:
    :return:
    """
    if request.method == 'DELETE':
        delivery_crew_group = get_object_or_404(Group, name='Delivery crew')
        user = get_object_or_404(User, id=pk)
        if user.groups.filter(name=delivery_crew_group).exists():  # if a delivery crew, remove/demote user
            user.groups.remove(delivery_crew_group)
            return Response({"message": f"<{user.username}> is demoted. No longer delivery crew."},
                            status.HTTP_204_NO_CONTENT)
        # inform if user is not a delivery
        return Response({"message": f"<{user.username}> is not delivery crew."}, status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def menu_items(request):  # /api/menu-items/
    """
    Manages menu items via this FBV (Function-Based View).

    Endpoint: /api/menu-items

    GET:
    Returns a list of all menu items.All users can list

    POST:
    Creates a new menu item. Only Managers can POST

    Parameters:
    - `request` (HttpRequest): The HTTP request object.

    Returns:
    - 200 OK: If the GET request is successful, it returns a list of all menu items.
    - 201 Created: If the POST request is successful, it returns the created menu item.
    - 400 Bad Request: If the POST request data is invalid, it returns an error response.

    Example POST Data:
    {
        "title": "New Item",
        "price": 9.99,
        "featured":"False" # Enclosed in quotes as a string
        "category_id": 1  # Replace with the actual category ID
    }

    Note:
    - To create a new menu item via POST, ensure the JSON data contains the required fields.
    - Use the 'category' field to specify the category ID to which the menu item belongs.
    """
    if request.method == 'GET':
        menuitems = MenuItem.objects.select_related('category').all()
        serialized_menu_items = MenuItemSerializer(menuitems, many=True)
        return Response(serialized_menu_items.data, status.HTTP_200_OK)
    if request.method == 'POST':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serialized_menuitem = MenuItemSerializer(data=request.data)  # Deserialize the JSON data
        serialized_menuitem.is_valid(raise_exception=True)  # validate data and throw an error if invalid
        serialized_menuitem.save()  # save data to db
        return Response(serialized_menuitem.data, status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_menu_item(request, pk):
    """
    Manages a single menu item via this FBV (Function-Based View).

    Endpoint: /api/menu-items/{pk}/

    GET:
    Returns details of a single menu item. All users(Managers, Customers(other users) and Delivery Crew)

    PUT:
    Replaces a menu item. Managers only

    PATCH:
    Updates a menu item. Managers only

    DELETE:
    Deletes a menu item. Managers only

    Parameters:
    - `request` (HttpRequest): The HTTP request object.
    - `pk` (int): The primary key of the menu item to operate on.

    Returns:
    - 200 OK: If the GET request is successful, it returns the details of the menu item.
    - 204 No Content: If the PUT or PATCH request is successful.
    - 400 Bad Request: If the PUT, or PATCH request data is invalid, it returns an error response.
    - 404 Not Found: If the menu item with the specified `pk` does not exist.

    Example PUT Data: (All fields must be included)
    {
        "title": "New Item",
        "price": 9.99,
        "featured": "false", # Enclose boolean in quotes as a string
        "category": 1  # Replace with the actual category ID
    }

    Example PATCH Data: (Only include field to update. If all fields are included then it acts as a PUT request)
    {
    "price": 11.99,
    "featured": "false" # Enclose boolean in quotes as a string
    }

    Note:
    - To PATCH a menu item, only include fields you want to update; for a PUT request, include all fields.
    - Use the 'category' field to specify the category ID to which the menu item belongs.
    - Ensure the JSON data adheres to field constraints and data types defined in your model.
    """
    menu_item = get_object_or_404(MenuItem, pk=pk)  # better way to query with error handling
    # menu_item = MenuItem.objects.get(pk=pk) # requires manual error handling incase pk doesn't exist
    if request.method == 'GET':
        serialized_menu_item = MenuItemSerializer(menu_item)
        return Response(serialized_menu_item.data, status.HTTP_200_OK)

    # Only Manager can PUT, PATCH and DELETE menu items
    # Stop further execution if user is not a manager
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = MenuItemSerializer(menu_item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PATCH':
        serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        menu_item.delete()
        return Response({'message': 'Resource deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart(request):
    """
    GET: Fetches all Cart items for the Current user.
    POST: Allows Current user to add menu items to their Cart
          Example POST payload:
              {
                "menuitem":"10",
                "quantity":"10"
              }
    :param request:
    :return: JSON() and Status Codes.
    """
    if request.method == 'GET':
        # Fetch cart items for the current user
        user_cart_items = Cart.objects.filter(user=request.user)  # Pass the authenticated user to the serializer
        user_cart_items_serialized = CartSerializer(user_cart_items, many=True)
        return Response(user_cart_items_serialized.data, status.HTTP_200_OK)
    if request.method == "POST":
        serialized_cart_items = CartSerializer(data=request.data,
                                               context={'request': request})  # Deserialize the JSON data
        # catch if user tries to add duplicates to their cart. This constraint is added in the Cart model.
        try:
            serialized_cart_items.is_valid(raise_exception=True)  # validate data and throw an error if invalid
            serialized_cart_items.save()  # Throws an error if unique constraint is not followed. This prevents duplicates
        except:
            menu_item = get_object_or_404(MenuItem, pk=request.data.get('menuitem'))
            return Response({"Error": f"No duplicates allowed. You already have {menu_item} in your cart, increase " 
                                      f"quantity instead."}, status.HTTP_400_BAD_REQUEST)
        return Response(serialized_cart_items.data, status.HTTP_201_CREATED)
