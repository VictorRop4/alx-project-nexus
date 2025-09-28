from django.utils import timezone
from rest_framework import viewsets, filters, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
import uuid

from .models import Category, Product, User, Order, Review, OrderItem, Payment
from .serializers import (
    CategorySerializer, ProductSerializer, RegisterSerializer, UserSerializer,
    OrderSerializer, ReviewSerializer, CheckoutSerializer, PaymentSerializer
)
from .permissions import RolePermission
from .pagination import StandardResultsSetPagination
from .mpesa import initiate_stk_push, MpesaClient

client = MpesaClient()
response = client.stk_push(phone_number="254708374149", amount=10)

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])  # Safaricom does not authenticate
def mpesa_callback(request):
    """
    Receive STK push callback from Safaricom.
    """
    data = request.data
    logger.info("M-Pesa Callback: %s", data)

    # Example: Save to database or log
    # You can parse request.data["Body"]["stkCallback"] for status and metadata

    return Response({"ResultCode": 0, "ResultDesc": "Callback received successfully"}, status=status.HTTP_200_OK)


# ------------------- CATEGORY -------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [RolePermission]
    pagination_class = StandardResultsSetPagination

    list_query_params = [
        openapi.Parameter('parent', openapi.IN_QUERY, description="Filter by parent ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search categories", type=openapi.TYPE_STRING),
        openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort by name or created_at", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
    ]

    @swagger_auto_schema(
        operation_description="Retrieve a list of categories with filtering, sorting, and pagination.",
        manual_parameters=list_query_params,
        responses={200: CategorySerializer(many=True)},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# ------------------- PRODUCT -------------------
class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [RolePermission]
    allowed_roles = [User.UserRole.SELLER, User.UserRole.ADMIN]
    owner_field = "seller"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "price"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    list_query_params = [
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('price', openapi.IN_QUERY, description="Filter by price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search products", type=openapi.TYPE_STRING),
        openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort by price, created_at", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
    ]

    @swagger_auto_schema(
        operation_description="Retrieve a list of products with filtering, sorting, and pagination.",
        manual_parameters=list_query_params,
        responses={200: ProductSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# ------------------- AUTH -------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account.",
        responses={201: RegisterSerializer()},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the profile of the authenticated user.",
        responses={200: UserSerializer()},
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def get_object(self):
        return self.request.user


# ------------------- ORDER -------------------
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"

    @swagger_auto_schema(
        operation_description="Place a new order. Calculates total automatically.",
        responses={201: OrderSerializer()},
    )
    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        order = self.get_object()
        if order.is_paid:
            return Response({"message": "Order already paid."}, status=status.HTTP_400_BAD_REQUEST)

        response = initiate_stk_push(order)
        return Response({"message": "Payment initiated", "mpesa_response": response})

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        order = self.get_object()
        if not order.is_paid:
            return Response({"error": "Order must be paid before delivery."}, status=status.HTTP_400_BAD_REQUEST)

        order.is_delivered = True
        order.save()
        return Response({"message": "Order marked as delivered."}, status=status.HTTP_200_OK)


# ------------------- PAYMENT -------------------
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"


# ------------------- REVIEW -------------------
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if not order.is_paid or not order.is_delivered:
            raise ValueError("You can only review products from paid and delivered orders.")
        serializer.save(user=self.request.user)


# ------------------- CHECKOUT -------------------
class CheckoutView(generics.GenericAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [RolePermission]
    allowed_roles = ["CUSTOMER"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data["items"]
        payment_method = serializer.validated_data["payment_method"]

        order = Order.objects.create(customer=request.user)

        total_amount = 0
        for item in items_data:
            product = Product.objects.get(pk=item["product"].id)
            quantity = item["quantity"]
            OrderItem.objects.create(
                order=order, product=product, quantity=quantity, price=product.price
            )
            total_amount += product.price * quantity

        order.total_amount = total_amount
        order.save()

        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=total_amount,
            status="pending",
            transaction_id=str(uuid.uuid4()),
        )

        if payment_method == "mpesa":
            phone = request.data.get("phone")
            if not phone:
                return Response({"error": "Phone number is required for M-Pesa"}, status=400)
            mpesa_response = stk_push(phone, total_amount, payment.transaction_id)
            return Response({
                "order_id": order.id,
                "total_amount": total_amount,
                "payment_id": payment.id,
                "payment_method": "mpesa",
                "mpesa_response": mpesa_response
            })

        return Response({
            "order_id": order.id,
            "total_amount": total_amount,
            "payment_id": payment.id,
            "payment_method": payment_method,
        })
    
# ------------------- M-PESA CALLBACKS -------------------
class MpesaCallbackView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        transaction_id = data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")
        result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode")
        amount = data.get("Body", {}).get("stkCallback", {}).get("CallbackMetadata", {}).get("Item", [{}])[0].get("Value")

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            if result_code == 0:
                payment.status = "successful"
                payment.paid_at = timezone.now()
                payment.save()

                order = payment.order
                order.status = "paid"
                order.save()
            else:
                payment.status = "failed"
                payment.save()
        except Payment.DoesNotExist:
            pass

        return Response({"status": "received"})


class MpesaSTKPushView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("phone_number", openapi.IN_QUERY, description="Customer phone number (2547...)", type=openapi.TYPE_STRING),
            openapi.Parameter("amount", openapi.IN_QUERY, description="Payment amount", type=openapi.TYPE_INTEGER),
        ],
        responses={200: "STK Push initiated successfully"}
    )
    def post(self, request):
        phone = request.query_params.get("phone_number")
        amount = request.query_params.get("amount")
        if not phone or not amount:
            return Response({"error": "phone_number and amount are required"}, status=400)

        client = MpesaClient()
        response = client.stk_push(phone, int(amount))
        return Response(response)
