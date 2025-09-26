from rest_framework import viewsets, filters
from .models import Category, Product, User, Order, Review
from .serializers import CategorySerializer, ProductSerializer,RegisterSerializer,UserSerializer
from rest_framework import generics, permissions
from rest_framework.response import Response
from .permissions import RolePermission
from .serializers import OrderSerializer, ReviewSerializer
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .pagination import StandardResultsSetPagination
# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    list_query_params = [
        openapi.Parameter('parent', openapi.IN_QUERY, description="Filter categories by parent category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search categories by name or description", type=openapi.TYPE_STRING),
        openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort categories by fields: name, created_at", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Pagination page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page", type=openapi.TYPE_INTEGER),
    ]
    @swagger_auto_schema(
        operation_description="Retrieve a list of categories with filtering, sorting, and pagination.",
        manual_parameters=list_query_params,
        responses={200: CategorySerializer(many=True)},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [RolePermission]
    allowed_roles =[User.UserRole.SELLER, User.UserRole.ADMIN]
    owner_field = "seller"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterSet_fields = ["category","price"]
    search_fields = ["name","description"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    list_query_params = [
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter products by category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('price', openapi.IN_QUERY, description="Filter products by price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search products by name or description", type=openapi.TYPE_STRING),
        openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort products by fields: price, created_at", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Pagination page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page", type=openapi.TYPE_INTEGER),
    ]

    @swagger_auto_schema(
        operation_description="Retrieve a list of products with filtering, sorting, and pagination.",
        manual_parameters=list_query_params,
        responses={200: ProductSerializer(many=True)},
    )
    
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)



class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes=[permissions.AllowAny]
    serializer_class = RegisterSerializer

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
        operation_description="Retrieve the profile of the currently authenticated user.",
        responses={200: RegisterSerializer()},
    )

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def get_object(self):
        return self.request.user

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes =[RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes =[RolePermission]
    allowed_roles = [User.UserRole.CUSTOMER]
    owner_field = "customer"


   