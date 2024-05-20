from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from users.models import UserProfile
from messaging.models import Message
from auctions.models import Bidder, Notification, Category
from django.db.models import Q, Count


def is_vendor(request):
    if request.user.is_authenticated:
        user = get_object_or_404(UserProfile, username=request.user)
        is_vendor = user.groups.filter(name='vendor').exists()

        return {'is_vendor': is_vendor}
    else:
        return {'is_vendor': None}
    

def is_read_count(request):
    msg = Message.objects.filter().last()

    if msg:
        if msg.sender == request.user:
            msg = Message.objects.filter(Q(sender=request.user.id), sender_read=False, recipient_read=True).count()
        else:
            msg = Message.objects.filter(Q(recipient=request.user.id), sender_read=True, recipient_read=False).count()
    return {'is_read_count': msg}


def my_bid_count(request):
    my_bid_count = Bidder.objects.filter(user=request.user.id, type='auction').count()
    return {'my_bid_count': my_bid_count}


def notification_count(request):
    notification_count = Notification.objects.filter(user=request.user.id, is_read=False).count()
    return {'notification_count': notification_count}


def notifications(request):
    notifications = Notification.objects.filter(user=request.user.id, is_read=False)
    return {'notifications': notifications}


def categories(request):
    categories = Category.objects.filter(status=True).order_by('-id')
    return {'categories': categories}