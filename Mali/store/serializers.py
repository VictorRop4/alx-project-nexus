from rest_framework import serializers
from .models import Category, Product, CustomerProfile, Order, Review, Payment, OrderItem
from django.contrib.auth import get_user_model


User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
    
        CustomerProfile.objects.create(user=user)
        return user

class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields ="__all__"

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

    def validate(self, data):
        order = data.get("order")
        if order.status != "delivered" or order.total_amount <= 0:
            raise serializers.ValidationError(
                "You can only review products from paid and delivered orders."
            )
        return data

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model =Payment
        fields = "__all__"

class CheckoutSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")
        return value
