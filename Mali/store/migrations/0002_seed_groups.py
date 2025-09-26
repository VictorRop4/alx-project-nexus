from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Product, Order

def create_groups_and_permissions(apps, schema_editor):
    # Roles
    roles = ['Customer', 'Seller', 'Admin']

    for role_name in roles:
        group, _ = Group.objects.get_or_create(name=role_name)

    # Assign product permissions to Seller
    seller_group = Group.objects.get(name='Seller')
    product_ct = ContentType.objects.get_for_model(Product)
    product_perms = Permission.objects.filter(content_type=product_ct)
    for perm in product_perms:
        seller_group.permissions.add(perm)

    # Assign order permissions to Customer
    customer_group = Group.objects.get(name='Customer')
    order_ct = ContentType.objects.get_for_model(Order)
    order_perms = Permission.objects.filter(content_type=order_ct)
    for perm in order_perms:
        customer_group.permissions.add(perm)

class Migration(migrations.Migration):
    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions),
    ]
