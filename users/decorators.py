from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


def vendor_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'vendor',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def customer_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'customer',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def profile_complete_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Check if the user is authenticated and if their profile is complete
        if request.user.is_authenticated and not request.user.is_profile_complete:
            # Redirect to the profile completion page
            messages.error(request, "Please complete your profile before making a Bid!")
            redirect_url = reverse('profile', args=[request.user.username])
            return redirect(redirect_url)
        return view_func(request, *args, **kwargs)
    return wrapped_view