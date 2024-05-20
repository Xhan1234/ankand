from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField  # Correct import


class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        # Specify the User model
        user = self._create_user(username=username, email=self.normalize_email(email), password=password, **extra_fields)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        # Change the 'role' field to 'administrator'
        extra_fields['role'] = 'administrator'

        # Specify the email field to be passed to _create_user
        email = self.normalize_email(email) if email else None

        # Ensure that a valid email is provided
        if not email:
            raise ValueError('The Email field must be set')

        # Similar to create_user, specify the User model
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(username, email, password, **extra_fields)

class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)  # Include email as a separate field
    paypal_recipient_email = models.EmailField(null=True, blank=True)
    stripe_account_id = models.CharField(max_length=150, null=True, blank=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    address = models.TextField(blank=True, null=True, default='')
    state = models.CharField(max_length=100, blank=True, null=True, default='')
    city = models.CharField(max_length=100, blank=True, null=True, default='')
    street = models.CharField(max_length=150, blank=True, null=True, default='')
    house = models.CharField(max_length=150, blank=True, null=True, default='')
    zip_code = models.CharField(max_length=10, blank=True, null=True, default='')
    postal_code = models.CharField(max_length=10, blank=True, null=True, default='')
    phone = PhoneNumberField(default='')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    role = models.CharField(max_length=15, choices=[('customer', 'Customer'), ('vendor', 'Vendor'), ('administrator', 'Administrator')], default='customer')
    business_name = models.CharField(max_length=100, blank=True, null=True, help_text="Leave blank if you are a customer.")
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    objects = CustomUserManager()
    backend = 'django.contrib.auth.backends.ModelBackend'
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']  # Remove 'email' from the required fields since it's already specified in CustomUserManager

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        else:
            return "/staticfiles/images/user/user.png"

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def __str__(self):
        return self.username

    def is_profile_complete(self):
        return all([self.first_name, self.last_name, self.state, self.city, self.street, self.house, self.zip_code, self.postal_code, self.phone, self.paypal_recipient_email, self.stripe_account_id])  # Check if required fields are not empty


# class VendorPaymentReceive(AbstractBaseUser, PermissionsMixin):
#     STATUS_CHOICES = [
#         (True, 'Active'),
#         (False, 'Deactive'),
#     ]
        
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     paypal_recipient_email = models.EmailField(null=True, blank=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
#     created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

#     def __str__(self):
#         return f'{self.paypal_recipient_email}'