from django.contrib import admin
from .models import *

class ContactAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'phone')
    readonly_fields = ('created_at', 'updated_at',)

class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'hour_before', 'status')
    readonly_fields = ('created_at', 'updated_at',)

admin.site.register(Slider)
admin.site.register(Contact, ContactAdmin)
admin.site.register(DeliveryCharge)
admin.site.register(NotificationMessage, NotificationMessageAdmin)
admin.site.register(PercentageGain)