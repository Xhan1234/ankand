from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views


urlpatterns = [
    path('checkout/', views.payment_checkout, name='checkout_payment'),
    path('create_payment/', views.create_payment, name='create_payment'),
    path('execute_payment/', views.execute_payment, name='execute_payment'),
    path('payment_failed/', views.payment_failed, name='payment_failed'),

    path('stripe/checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('stripe/success/', views.success, name='success'),
    path('stripe/cancel/', views.cancel, name='cancel'),

    ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)