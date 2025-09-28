from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from decimal import Decimal

# -----------------------------
# User & Profile
# -----------------------------
class User(AbstractUser):
    class UserRole(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        SELLER = "seller", "Seller"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    default_address = models.CharField(max_length=255, blank=True, null=True)  # Later: make Address model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -----------------------------
# Catalog (Categories & Products)
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True,db_index=True) # Database indexing
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Database indexing
    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            ]

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)  # Stock Keeping Unit
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255,db_index=True) # Database indexing
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="KES")
    stock_quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True) # Database indexing
    updated_at = models.DateTimeField(auto_now=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

# Database indexing
    class Meta:
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
        ]

    def update_average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(models.Avg("rating"))["rating__avg"]
            self.average_rating = round(avg, 2)
        else:
            self.average_rating = 0.00
        self.save(update_fields=["average_rating"])


    def __str__(self):
        return self.name


# -----------------------------
# Cart & Cart Items
# -----------------------------
class Cart(models.Model):
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.customer}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


# -----------------------------
# Orders & Order Items
# -----------------------------

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    products = models.ManyToManyField("Product", through="OrderItem")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)

    def calculate_total(self):
        total = sum([item.quantity * item.product.price for item in self.items.all()])
        self.total_amount = total
        self.save()
        return total

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot at checkout

    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} × {self.product.name if self.product else 'Deleted Product'}"


# -----------------------------
# Payments
# -----------------------------
class Payment(models.Model):
    METHOD_CHOICES = [
        ("mpesa", "M-Pesa"),
        ("card", "Credit/Debit Card"),
        ("paypal", "PayPal"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order = models.ForeignKey(Order, related_name="payments", on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"

# -----------------------------
# Shipping
# -----------------------------
class Shipping(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
    ]

    order = models.OneToOneField(Order, related_name="shipping", on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    shipping_method = models.CharField(max_length=50, default="standard")
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipping for Order {self.order.id}"
    

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # values like 1–5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")  # each user can review a product once
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}★ by {self.user.username} on {self.product.name}"
