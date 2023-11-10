# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import IsAuthenticated
from .permissions import IsManager

# import model
from .models import MenuItem, Category
from .serializers import MenuItemSerializer, UserSerializer


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
def get_user_details(request):
    """
    Fetch details of the authenticated user
    :param request:
    :return: user details
    """
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
    })


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

