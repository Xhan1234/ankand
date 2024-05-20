from django.contrib.auth.forms import UserCreationForm
from django import forms
from users.models import UserProfile
from .widgets import StateWidget, CityWidget

# Define the choices for the 'role' field
ROLE_CHOICES = [
    ('customer', 'Customer'),
    ('vendor', 'Vendor'),
]

class CreateUserForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    business_name = forms.CharField(max_length=100, required=False, help_text="Leave blank if you are a customer.")

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password1', 'password2', 'role','business_name']


class EditUserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(widget=forms.FileInput, required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'address', 'phone', 'state', 'city', 'street', 'zip_code','postal_code', 'house', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'state': StateWidget(),  # Use the custom StateWidget for the 'state' field
            'city': CityWidget(),    # Use the custom CityWidget for the 'city' field
        }


class EditVendorPaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['paypal_recipient_email', 'stripe_account_id']
