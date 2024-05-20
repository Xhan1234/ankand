# middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if the user is authenticated and if their profile is complete
        if request.user.is_authenticated and not request.userprofile:
            # Redirect to the profile completion page
            if request.path != reverse('profile_completion'):
                return redirect('profile_completion')
        return response
