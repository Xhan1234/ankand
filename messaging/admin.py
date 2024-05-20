from django.contrib import admin
from .models import Message, MessageDetails

# Register your models here.
admin.site.register(Message)
admin.site.register(MessageDetails)
