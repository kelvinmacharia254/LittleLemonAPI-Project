from rest_framework import serializers

from django.contrib.auth.models import User

from .models import (
    MenuItem,
    Category
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
