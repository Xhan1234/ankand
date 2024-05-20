from .models import *
from django import forms
from django.forms import ModelForm
from users.widgets import StateWidget, CityWidget


class ProductSearchForm(forms.Form):
    query = forms.CharField(label='Search')

    
class CreateAuctionForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'category', 'description', 'details_description', 'type', 'price', 'reserve_price', 'bid_increments', 'direct_buy', 'quantity', 'image', 'image1', 'image2', 'condition', 'expired_date', 'status']
        widgets = {
            'expired_date':forms.TextInput(attrs={'type':'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['direct_buy'].required = False
        self.fields['reserve_price'].required = False
        self.fields['price'].required = False
    
    # def clean_direct_buy(self):
    #     direct_buy = self.cleaned_data['direct_buy']
    #     if direct_buy is not None and direct_buy < 1:
    #         raise forms.ValidationError("Direct Buy value must be at least 1.")
    #     return direct_buy


class OrderForm(forms.Form):
    auction_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1)
    paid_amount = forms.IntegerField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone = forms.CharField()
    email = forms.CharField()
    street = forms.CharField()
    state = forms.CharField()
    house = forms.CharField()
    postal_code = forms.CharField()
    zip_code = forms.CharField()
    address=forms.CharField()


class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea)


class BillingAddressForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    phone = PhoneNumberField()

    class Meta:
        model = BillingAddress
        fields = ['first_name', 'last_name', 'email', 'address', 'phone', 'state', 'city', 'street', 'zip_code','postal_code', 'house', 'same_as_shipping']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ShippingAddressForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    phone = PhoneNumberField()

    class Meta:
        model = ShippingAddress
        fields = ['first_name', 'last_name', 'email', 'address', 'phone', 'state', 'city', 'street', 'zip_code','postal_code', 'house']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            field.required = False


class ReviewForm(forms.ModelForm):
	class Meta:
		model = Review
		fields = ("comment","rate")