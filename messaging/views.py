from django.shortcuts import render, redirect, get_object_or_404
from .models import Message, MessageDetails
from .forms import MessageForm
from django.contrib.auth.decorators import login_required
from users.models import UserProfile
from datetime import datetime
from django.db.models import Q, Count
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages


# Create your views here.
@login_required()
def index(request):
    message_list = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('created_at')    
    message_list = message_list.annotate(unread=Count('messagedetails', filter=Q(messagedetails__read=False, messagedetails__recipientdetails=request.user)))

    return render(request, 'messaging/index.html', {
        'message_list': message_list
    })

def message_details(request, id):
    msg = Message.objects.get(id=id)
    message_details = MessageDetails.objects.filter(message=msg).order_by('created_at')  
    message_list = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('created_at')
    message_list = message_list.annotate(unread=Count('messagedetails', filter=Q(messagedetails__read=False, messagedetails__recipientdetails=request.user)))

    last = message_details.last()
    if last.recipientdetails == request.user:
        # Save read true
        msg.sender_read = True
        msg.recipient_read = True
        msg.save()

        # Iterate through each message and print the unread count
        for details in message_details:
            details.read = True
            details.save()

    context = {
        'message': msg,
        'message_list': message_list,
        'message_details': message_details,
    }

    return render(request, 'messaging/index.html', context)



def message_post(request, id):
    msg = Message.objects.get(id=id)
    message_details = MessageDetails.objects.filter(message=msg).order_by('created_at')  
    message_list = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('created_at')
    message_list = message_list.annotate(unread=Count('messagedetails', filter=Q(messagedetails__read=False, messagedetails__recipientdetails=request.user)))

    if request.method == 'POST':
        message_details_text = request.POST.get('message_details')
        if message_details_text:
            if msg.sender == request.user:
                MessageDetails.objects.create(
                    message=msg,
                    message_details=message_details_text,
                    senderdetails=request.user,
                    recipientdetails=msg.recipient
                )
                msg.recipient_read = False
                msg.sender_read = True
                msg.save()
            else:
                MessageDetails.objects.create(
                    message=msg,
                    message_details=message_details_text,
                    senderdetails=request.user,
                    recipientdetails=msg.sender
                )
                msg.recipient_read = True
                msg.sender_read = False
                msg.save()

            messages.success(request, f"Message has been sent!")

    context = {
        'message': msg,
        'message_list': message_list,
        'message_details': message_details,
    }

    return render(request, 'messaging/index.html', context)



def message_delete(request, id):
    try:
        msg = Message.objects.get(id=id)
        msg.delete()
    except msg.DoesNotExist:
        raise Http404("Msg does not exist")

    message_list = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('created_at')    
    message_list = message_list.annotate(unread=Count('messagedetails', filter=Q(messagedetails__read=False, messagedetails__recipientdetails=request.user)))

    return render(request, 'messaging/index.html', {
        'message_list': message_list
    })