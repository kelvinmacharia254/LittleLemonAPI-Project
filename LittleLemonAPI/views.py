# Create your views here.
from django.utils import timezone

from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle

from django.core.paginator import Paginator, EmptyPage

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsManager, IsCustomer

# import models
from .models import (
    MenuItem,
    Category,
    Cart,
    Order,
    OrderItem
)

from .serializers import (
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderItemSerializer,
    OrderSerializer,
)

from django.contrib.auth.models import User, Group


# User management and Authentication Endpoints.
@api_view(['POST'])
def signup(request):
    """
    Allows new user to register themselves with username,email and password.
    Endpoint: /api/users
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
def user_details(request):
    """
    Fetch details of the authenticated user
    Endpoint: /api/users/me
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
@permission_classes([IsManager])
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

        # use try statement incase you need custom message.
        # et_object_or_404 handles errors automatically so need of try statement
        try:
            user = get_object_or_404(User, username=username)
        except Http404:
            return Response({"message": f"User with username '{username}' not found."}, status.HTTP_404_NOT_FOUND)

        # Get the 'Manager' group
        manager_group = Group.objects.get(name='Manager')
        if user.groups.filter(name=manager_group).exists():  # inform if the user is already a manager
            return Response({"message": f"The user {user} is already a manager."}, status.HTTP_204_NO_CONTENT)
        else:  # Add user to Manager
            user.groups.add(manager_group)
            return Response({"message": f"You promoted {user} to a manager."}, status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsManager])
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
            return Response({"message": f"{user.username} is demoted. No longer manager."}, status.HTTP_200_OK)
        # inform if user is not a manager
        return Response({"message": f"{user.username} is not a manager."}, status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@permission_classes([IsManager])
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
            return Response({"message": f"The user {user} is already a delivery crew."}, status.HTTP_204_NO_CONTENT)
        else:  # Add user to Manager
            user.groups.add(delivery_crew_group)
            return Response({"message": f"You promoted {user} to a delivery crew."}, status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsManager])
def unassign_deliver_crew(request, pk):  # Endpoint/groups/delivery-crew/users/<int:pk>
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
@throttle_classes([UserRateThrottle])
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

        # implement filtering of menu items using title
        price = request.query_params.get('price')
        if price:  # filter by title
            menuitems = menuitems.filter(title=price)

            # Fetch search criteria passed as a query param
        search = request.query_params.get('search')
        if search:  # implement searching
            # menuitems = menuitems.filter(title__istartswith=search) # 'i' makes the search case-insensitive
            menuitems = menuitems.filter(title__icontains=search)  # 'i' makes the search case-insensitive

            # Fetch ordering criteria passed as a query param
        ordering = request.query_params.get('ordering')
        if ordering:  # implement ordering
            menuitems = menuitems.order_by(ordering)
                # ordering with multiple criteria
            # ordering_fields = ordering.split(",")  # split the query string
            # menuitems = menuitems.order_by(*ordering_fields)  # such by unpacking the list

            # pagination
        perpage = request.query_params.get('perpage', default=2)  #
        page = request.query_params.get('page', default=1)  #
        paginator = Paginator(menuitems, per_page=perpage)
        try:
            menuitems = paginator.page(number=page)
        except EmptyPage:  # Deal with an empty page
            menuitems = []

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


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsCustomer])
def cart(request):
    """
    Endpoint: /api/cart/menu-items
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
        user_cart_items = Cart.objects.filter(user=request.user)
        user_cart_items_serialized = CartSerializer(user_cart_items, many=True)
        return Response(user_cart_items_serialized.data, status.HTTP_200_OK)

    if request.method == "POST":
        serialized_cart_items = CartSerializer(data=request.data,
                                               context={
                                                   'request': request})  # Deserialize the JSON data and pass the ...
        # ...authenticated user to the serializer

        # catch if user tries to add duplicates to their cart. This constraint is defined in the Cart model.
        try:
            serialized_cart_items.is_valid(raise_exception=True)  # validate data and throw an error if invalid
            serialized_cart_items.save()  # Throws an error if unique constraint is not followed. ...
            # ... This prevents duplicates
            # Error thrown during saving because, the constraint is set on the db schema
        except Http404:
            menu_item = get_object_or_404(MenuItem, pk=request.data.get('menuitem'))
            return Response({"Error": f"No duplicates allowed. You already have {menu_item} in your cart, increase "
                                      f"quantity instead."}, status.HTTP_400_BAD_REQUEST)
        return Response(serialized_cart_items.data, status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        # Fetch cart items for the current user
        user_cart_items = Cart.objects.filter(user=request.user)
        user_cart_items.delete()
        return Response({"Message": "All Items have been deleted from the Cart."}, status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_manager(request):
    """
    ndpoint: /api/orders/
    GET:
        1. Manager: Returns all orders with order items by all users.
        2. Customers: Returns their orders and items in each order
        3. Delivery crew: Returns orders and items contained for orders assigned to them
    POST:
        1. Customers: Place the order of items in their cart
    :param request:
    :return:
    """
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            # For a manager, display order items for all users
            orders = Order.objects.all()
        elif request.user.groups.filter(name='Delivery crew').exists():
            # For a delivery crew, display orders assigned to them
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            # For a normal user, display items in their orders
            orders = Order.objects.filter(user=request.user)

        # Serialize order details for manager and Delivery crew
        serialized_orders = []
        for order in orders:
            user_order_items = OrderItem.objects.filter(order=order)
            serialized_order_items = OrderItemSerializer(user_order_items, many=True)
            serialized_orders.append({'order_id': order.id, 'order_items': serialized_order_items.data})

        return Response(serialized_orders, status=status.HTTP_200_OK)

    if request.method == 'POST':  # order creation
        # Carts only belongs to Customers.
        # Enforce in cart creation endpoint i.e. /api/cart/menu-items
        user_cart_items = Cart.objects.filter(user=request.user)
        if user_cart_items.exists():
            # Create a new order
            new_order = Order.objects.create(user=request.user, status=False, total=0, date=timezone.now())
            total_price = 0

            # Create OrderItems and associate them with the new order
            for cart_item in user_cart_items:
                # Populate order items with all items from the cart
                order_item = OrderItem.objects.create(
                    order=new_order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    price=cart_item.price
                )
                total_price += cart_item.price

            # Update the total price for the new order
            new_order.total = total_price
            new_order.save()

            # Delete Cart items after adding to the order
            user_cart_items.delete()

            return Response({"Message": "Order created"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"Message": "Your cart is empty. Add items to Cart to proceed."},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_order_manager(request, pk):
    """
    Endpoint: /api/orders/{orderId}E
    Uses:
    1. Customer:
        GET
       - Return all items of the order id of the current user
       - Display appropriate error HTTP error status code if the order id doesn't belong to current user.
    2. Manager:
        PUT, PATCH
       - Assign Delivery crew to the order
       - Update delivery status to 0 or 1
       - Delete order
    3. Delivery crew
         PATCH
       - Update delivery status to 0 or 1
       Example1 PATCH LOAD:
            {
                "status":"1",
                "delivery_crew":"2"
            }
        Example2 PATCH LOAD: Setting Delivery crew to None
            {
                "status":"0",
                "delivery_crew":""
            }
    :param request:
    :return: JSON and Status Code
    """
    order = get_object_or_404(Order, pk=pk)  # get order by id
    if request.method == 'GET':
        if not request.user.groups.exists():
            # Only own orders and can list items in their orders
            # check if the orders belongs to the request user
            if order.user == request.user:
                order_items = OrderItem.objects.filter(order=order)
                serialized_order_items = OrderItemSerializer(order_items, many=True)
                serialized_orders = [{'order_id': order.id, 'order_items': serialized_order_items.data}]
                return Response(serialized_orders, status.HTTP_200_OK)
            else:
                return Response({"message": f"{request.user} has no orders"}, status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Only Customer users can have orders."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        user = request.user  # Fetch user
        groups = user.groups.values_list('name', flat=True)  # Fetch group fo the user
        allowed_groups = {'Manager', 'Delivery crew'}

        # True if no intersection(no group).
        # False if there is an intersection(group either manager or Delivery crew)
        if not allowed_groups.intersection(groups):
            return Response(
                {"message": "Access Forbidden. Manager or Delivery crew privileges required to access."},
                status=status.HTTP_403_FORBIDDEN)

        # Validate the incoming data based on the user's group.
        # Context must be passed to serializer to ensure PATCH is do for the right group.
        # PATCH fields for either Manager or Delivery crew defined in the serializer's validate method.
        serialized_input = OrderSerializer(
            instance=order, data=request.data, context={'request': request}, partial=True
        )
        serialized_input.is_valid(raise_exception=True)
        serialized_input.save()

        return Response(serialized_input.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            order.delete()
            return Response({"message": f"Order {pk} deleted."}, status=status.HTTP_204_NO_CONTENT)
