from django.contrib import admin
from .models import *

class UserByRoleAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'phone', 'role','email','state','city','street','zip_code')
    list_filter = ('role','state','city','street','zip_code',)

# Register the UserProfile model with the custom admin class
admin.site.register(UserProfile, UserByRoleAdmin)

