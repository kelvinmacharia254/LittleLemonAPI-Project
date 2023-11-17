from rest_framework import serializers

from django.contrib.auth.models import User

from .models import (
    MenuItem,
    Category,
    Cart,
    OrderItem,
)


# User management and Authentication serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']

    # def update(self, instance, validated_data):
    #     # Set partial=True for the update method
    #     return super().update(instance, validated_data, partial=True)


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']

        # This fields are not expected to be passed in a POST request payload
        read_only_fields = ['user', 'price',
                            'unit_price']  # Cart Item Id/pk is added automatically.

    def create(self, validated_data):
        user = self.context['request'].user  # user context passed from view. Associates Cart item to user
        menuitem = validated_data.pop('menuitem')  # Extract MenuItem ID from POST data
        # menuitem = MenuItem.objects.get(pk=menuitem_id)
        unit_price = menuitem.price  # Fetch unit_price from MenuItem model

        quantity = validated_data.get('quantity')
        price = unit_price * quantity  # Calculate price

        # Create Cart instance with calculated price
        cart_item = Cart.objects.create(user=user, menuitem=menuitem, unit_price=unit_price, price=price,
                                        **validated_data)

        return cart_item


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']
