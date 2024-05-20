from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.index, name='message'),
    path('messages/<str:id>', views.message_details, name='message-details'),
    path('messages-post/<str:id>', views.message_post, name='message-post'),
    path('messages-delete/<str:id>', views.message_delete, name='message-delete'),
]
