from django.db import models
from users.models import UserProfile
from auctions.models import Auction


class Message(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, null=False, blank=False, default='')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="Sender")
    sender_read = models.BooleanField(default=True)
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="Receiver")
    recipient_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.recipient.username

class MessageDetails(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    message_details = models.TextField()
    senderdetails = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="Senderdetails", null=True, blank=True)
    recipientdetails = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="Receiverdetails", null=True, blank=True)
    read = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message_details
