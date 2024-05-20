from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login', auth_views.LoginView.as_view(template_name='users/auth/login.html'), name='login'),
    path('logout', views.user_logout ,name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('change/password/', views.change_password, name='change-password'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/auth/password-reset/password_reset_form.html',
        html_email_template_name='users/auth/password-reset/html_password_reset_email.html',
        subject_template_name='users/auth/password-reset/password_reset_subject.txt',
        success_url='/password_reset_done/'
    ), name='password-reset'),

    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/auth/password-reset/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/auth/password-reset/password_reset_confirm.html',
        success_url='/password_reset_complete/'
    ), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/auth/password-reset/password_reset_complete.html'
    ), name='password_reset_complete'),

    # User Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    path('profile/payment-settings/<str:username>/', views.profile_payment_settings, name='profile-payment-settings'),
]