from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from .models import UserProfile
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from users.forms import EditUserProfileForm, EditVendorPaymentSettingsForm
from auctions.models import Auction
from auctions.models import Bidder
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


def register(request):
    """
    This function handles user registration by processing the registration form.
    If the user is already authenticated, redirect them to their profile. Otherwise, if the user's http method is POST then 
    it will create a new user otherwise it will show a registration from.
    You don't need to create another UserProfile instance here. Already created the user with the instances.
    HTTP Method: POST
    """
    # If the user is already authenticated, redirect them to their profile.
    if request.user.is_authenticated:
        return redirect(reverse('personal_profile', args=[request.user.username]))
    
    # Otherwise, Create new User
    else:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password1')
                role = form.cleaned_data.get('role')
                business_name = form.cleaned_data.get('business_name')

                user = UserProfile.objects.create_user(
                    username=username, 
                    email=email, 
                    password=password, 
                    role=role,
                    business_name=business_name)

                # if role == 'customer':
                #     group_name = 'customer'
                # elif role == 'vendor':
                #     group_name = 'vendor'
                # else:
                #     group_name = 'administrator'

                # group, created = Group.objects.get_or_create(name=group_name)
                # group.user_set.add(user)

                # Determine group based on role and add user to it
                group_name = {'customer': 'customer', 'vendor': 'vendor', 'administrator': 'administrator'}.get(role, 'customer')
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(user)

                login(request, user)

                messages.success(request, 'Account was created for ' + user.username)
                return redirect('dashboard')
        else:
            form = CreateUserForm()

        context = {
            'form': form
            }
        
        return render(request, 'users/auth/register.html', context)


@login_required()
def user_logout(request):
    """
    This function allows a logged-in user to loggout.
    HTTP Method: GET
    """
    logout(request)
    return redirect('login')


@login_required()
def profile(request, username):
    """
    This function allows a logged-in user to update their profile information.
    If method is POST then Validate the submitted user update form (EditUserProfileForm).
    If the form is valid save the user update form to update user details. Save the profile update form to update profile details.
    Then redirect the user back to the 'profile' page. 
    And If not POST: Create instances of EditUserProfileForm for rendering the profile update form.
    It must needed to login user.
    HTTP Method: POST
    """
        
    try:
        user_profile = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to edit this profile.')
        return redirect('profile_view')

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=username)
    else:
        form = EditUserProfileForm(instance=user_profile)

    context = {
        'form': form,
        'user_data': user_profile,
    }

    return render(request, 'dashboard/_preview/_profile.html', context)


@login_required
def change_password(request):
    """
    This function allows a logged-in user to change their password.
    If the form is valid then save the form to update the user's password. Update the session authentication hash. Display a success message.
    And redirect the user back to the 'user profile' page. Otherwise, display an error message.
    HTTP Method: POST
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile', user)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/auth/change-password.html', {
        'form': form
    })

@login_required()
def dashboard(request):
    """
    This function renders the dashboard page for a logged-in user.
    With `auction_count`, `bid_count` & `winning_bid_count`
    It must needed to login user.
    HTTP Method: GET
    """
    user = get_object_or_404(UserProfile, username=request.user)
    auction_count = Auction.objects.filter(author=user).count()
    bid_count = Bidder.objects.filter(user=user, type='auction').count()

    auctions = Auction.objects.filter(closed=True)
    # Now find the winningBid is equal to me
    myWins = []
    for aucs in auctions:
        # Are there any winning bids on this auction?
        if aucs.winnerBid:
            # Am i the winning bid?
            if aucs.winnerBid.user == request.user:
                myWins.append(aucs)

    return render(request, 'dashboard/_preview/_dashboard.html',
                  {
                      'user': user,
                      'auction_count': auction_count, 
                      'my_bid_count': bid_count,
                      'winning_bid_count': len(myWins)
                      })


def profile_payment_settings(request, username):

    user_profile = UserProfile.objects.get(username=username)

    if request.method == 'POST':
        form = EditVendorPaymentSettingsForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=username)
    else:
        form = EditVendorPaymentSettingsForm(instance=user_profile)

    context = {
        'form': form,
        'user_data': user_profile,
    }

    return render(request, 'dashboard/_preview/_payment_settings.html', context)
