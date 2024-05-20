import uuid
from django.shortcuts import render
import paypalrestsdk
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from users.models import UserProfile
from django.http import HttpResponseRedirect
from auctions.models import Auction, Order, Invoice, BillingAddress, Bidder
from paypalrestsdk import Sale, Payout, ResourceNotFound
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse

# Create your views here.
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})

def make_payout(recipient_email, amount, currency='USD'):
    payout_item = {
        "recipient_type": "EMAIL",
        "amount": {
            "value": str(amount),
            "currency": currency
        },
        "receiver": str(recipient_email),
        "note": "Payment from your website"
    }

    payout = Payout({
        "sender_batch_header": {
            "sender_batch_id": "batch_" + str(uuid.uuid4())[:8],
            "email_subject": "You have a payout!"
        },
        "items": [payout_item]
    })

    try:
        payout_created = payout.create()
        return payout_created
    except ResourceNotFound as error:
        print(error)
        return None


def create_payment(request):
    paid_amount = request.POST.get('paid_amount')
    delivery_fee = request.POST.get('delivery_fee')
    percentage_price = request.POST.get('percentage_price')
    paymentMethod = request.POST.get('paymentMethod')
    product_slug = request.POST.get('product_slug')
    billing_profile = request.POST.get('billing_profile')
    type = request.POST.get('type')
    user = request.user

    product = get_object_or_404(Auction, slug=product_slug)
    userdetails = UserProfile.objects.get(username=user)
    same = Order.objects.filter(user=userdetails, auction=product)
   
    recipient_email = product.author.paypal_recipient_email
    payout_amount = float(paid_amount) - float(percentage_price)
    
    if product.quantity < 1:
        messages.error(request, "Product Quantity Not Available!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    if same:
        messages.error(request, "You already ordered this product!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('execute_payment')
                                                     + '?paid_amount=' + str(paid_amount)  
                                                     + '&recipient_email=' + str(recipient_email) 
                                                     + '&payout_amount=' + str(payout_amount)
                                                     + '&product_slug=' + str(product_slug)
                                                     + '&billing_profile=' + str(billing_profile)
                                                     + '&type=' + str(type)),
            "cancel_url": request.build_absolute_uri(reverse('payment_failed')),
        },
        "transactions": [
            {
                "amount": {
                    "total": paid_amount,  # Total amount in USD
                    "currency": "USD",
                },
                "description": product.type,
            }
        ],
    })

    if payment.create():
        return redirect(payment.links[1].href)  # Redirect to PayPal for payment
    else:
        return render(request, 'payments/payment_failed.html')
    


def confirm_order_after_payments(user, product_slug, paid_amount, paymentMethod, billing_profile, type):
    product = get_object_or_404(Auction, slug=product_slug)
    userdetails = UserProfile.objects.get(username=user)
    billing = get_object_or_404(BillingAddress, pk=billing_profile)

    with transaction.atomic():
        order = Order.objects.create(
            auction=product,
            product_type=type, 
            user=userdetails, 
            billing=billing, 
            payment_method=paymentMethod, 
            quantity=1, 
            paid_amount=paid_amount,
            balance_type='debit',
            )
        Invoice.objects.create(user=userdetails, order=order)
        bid = Bidder.objects.filter(auction=product, user=userdetails, type=type, winningBid=True).last()
        if bid:
            bid.paid_status = True
            bid.save()

        if type == 'direct_buy':
            product.quantity = product.quantity - 1
        product.winnerBid = bid
        product.closed = True
        product.status = False
        product.save()

        if product.quantity != 0:
            product.closed = False
            product.status = True
            product.save()

        if paymentMethod == "credit_card":
            order.paid = True
            order.save()
        elif paymentMethod == "paypal":
            order.paid = True
            order.save()
        else:
            order.paid = False
            order.save()


def execute_payment(request):
    user = request.user
    product_slug =request.GET.get('product_slug') 
    paid_amount = request.GET.get('paid_amount')
    billing_profile = request.GET.get('billing_profile')
    type = request.GET.get('type')
    recipient_email = request.GET.get('recipient_email')
    payout_amount = request.GET.get('payout_amount')
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        make_payout(recipient_email, payout_amount)
        confirm_order_after_payments(user, product_slug, paid_amount, 'credit_card', billing_profile, type)
        return render(request, 'payments/payment_success.html')
    else:
        return render(request, 'payments/payment_failed.html')



def payment_checkout(request):
    return render(request, 'checkout.html')


def payment_failed(request):
    return render(request, 'payments/payment_failed.html')




# Stripe Payment Integrations
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    paid_amount = request.POST.get('paid_amount')
    percentage_price = request.POST.get('percentage_price')
    product_slug = request.POST.get('product_slug')
    billing_profile = request.POST.get('billing_profile')
    type = request.POST.get('type')
    user = request.user
    product = get_object_or_404(Auction, slug=product_slug)
    userdetails = UserProfile.objects.get(username=user)
    same = Order.objects.filter(user=userdetails, auction=product)
    receiver_stripe_account = product.author.stripe_account_id
    paid_amount_in_cents = int(float(paid_amount) * 100)

    if product.quantity < 1:
        messages.error(request, "Product Quantity Not Available!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    if same:
        messages.error(request, "You already ordered this product!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # Create a new Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.title,
                    },
                    'unit_amount': paid_amount_in_cents,  # Amount in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('success') 
                                               + '?paid_amount=' + str(paid_amount)  
                                               + '&percentage_price=' + str(percentage_price) 
                                               + '&receiver_stripe_account=' + str(receiver_stripe_account)
                                               + '&product_slug=' + str(product_slug)
                                               + '&billing_profile=' + str(billing_profile)
                                               + '&type=' + str(type)),
        cancel_url=request.build_absolute_uri(reverse('cancel')),
    )
    if session:
        return redirect(session.url)
    else:
        return render(request, 'payments/stripe-payment/cancel.html')

def success(request):
    user = request.user
    product_slug =request.GET.get('product_slug') 
    paid_amount = request.GET.get('paid_amount')
    billing_profile = request.GET.get('billing_profile')
    type = request.GET.get('type')
    confirm_order_after_payments(user, product_slug, paid_amount, 'credit_card', billing_profile, type)
    return render(request, 'payments/stripe-payment/success.html')

def cancel(request):
    return render(request, 'payments/stripe-payment/cancel.html')