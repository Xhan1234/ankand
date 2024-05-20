from auctions.models import auction  # Replace with your actual model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction  # Import transaction module

@transaction.atomic  # Use transaction.atomic to ensure all changes are saved or none
def run():
    # Define custom permissions with the correct codenames
    add_auction_permission, _ = Permission.objects.get_or_create(
        codename='auctions.add_auction',
        name='Can add auction',
        content_type=ContentType.objects.get_for_model(auction)
    )

    buy_auction_permission, _ = Permission.objects.get_or_create(
        codename='auctions.buy_auction',
        name='Can buy auction',
        content_type=ContentType.objects.get_for_model(auction)
    )

    # Assign permissions to groups as needed
    vendor_group = Group.objects.get(name='vendor')
    customer_group = Group.objects.get(name='customer')

    vendor_group.permissions.add(add_auction_permission, buy_auction_permission)
    customer_group.permissions.add(buy_auction_permission)

if __name__ == "__main__":
    run()
