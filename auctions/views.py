import io
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils import timezone
from django.urls import reverse
from .forms import CreateAuctionForm, OrderForm
from .models import Auction, Order, ShippingAddress, Bidder, Comment
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from decimal import Decimal
from django.db import transaction
from django.template.loader import get_template
from xhtml2pdf import pisa
from users.models import UserProfile
from django.http import Http404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.mail import send_mail
from users.decorators import vendor_required, customer_required, profile_complete_required
from django.core.paginator import Paginator
from datetime import datetime
from .forms import *
from website.models import DeliveryCharge, NotificationMessage, PercentageGain
from messaging.models import Message, MessageDetails
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse



# auctions Lists
@vendor_required
def auctions(request):
    auctions = Auction.objects.filter(author=request.user).order_by('-id')
    paginator = Paginator(auctions, 10) # Show 10 items per page    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'dashboard/_preview/_auctions.html', context)


# Create auction
@login_required
@vendor_required
def auction_add(request):
    # Check if the user belongs to the "vendor" group
    vendor_group = Group.objects.get(name='vendor')
    # return HttpResponse(vendor_group)
    is_vendor = vendor_group in request.user.groups.all()

    if request.method == 'POST':

        if is_vendor:  # Check if the user is a vendor before processing the form
            form = CreateAuctionForm(request.POST, request.FILES)
            if form.is_valid():
                price = request.POST.get("price")
                type = request.POST.get("type")
                auction = form.save(commit=False)
                auction.author = request.user
                if type == 'auction' or type == 'auction & buy-it-now':
                    auction.started_price = price
                auction.save()

                status = request.POST.get("status")
                auction_open = get_object_or_404(Auction, id=auction.id)

                if status == 'True':
                    auction_open.open_status = auction_open.open_status + 1
                    auction_open.closed = False
                elif status == 'False':
                    auction_open.open_status = 0
                    auction_open.closed = True
                auction_open.save()
                
                return redirect('auctions')
        else:
            return redirect('personal_profile', username=request.user.username)
    else:
        form = CreateAuctionForm()

    return render(request, 'auctions/create.html', {'form': form, 'is_vendor': is_vendor})


# Update auction
@login_required
@vendor_required
def auction_edit(request, slug):
    auction = get_object_or_404(Auction, slug=slug)
    if request.method == 'POST':
        form = CreateAuctionForm(request.POST, request.FILES, instance=auction)
        if form.is_valid():
            auction = form.save(commit=False)
            status = request.POST.get("status")
            expired_date = request.POST.get("expired_date")

            original_datetime_str = str(timezone.now())
            original_datetime = datetime.fromisoformat(original_datetime_str)
            formatted_datetime_str = original_datetime.replace(microsecond=0).isoformat()

            if status == 'True':
                if formatted_datetime_str < expired_date:
                    auction.open_status = auction.open_status + 1
                    auction.closed = False
                    auction.winnerBid = None
                    auction.status = True
                else:
                    messages.error(request, "Expired datetime should be greated then current datetime!")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif status == 'False':
                auction.closed = True
                auction.winnerBid = None
                auction.status = False
            
            auction.save()

            return redirect('auctions')
    else:
        form = CreateAuctionForm(instance=auction)
    return render(request, 'auctions/create.html', {'form': form, 'auction': auction})


# Delete auction
@login_required
def auction_delete(request, slug):
    try:
        auction = Auction.objects.get(slug=slug)
        auction.delete()
    except auction.DoesNotExist:
        raise Http404("auction does not exist")
    return redirect('auctions')


# Read auction
# views.py
@login_required
def auction_details(request, slug):
    check_expired_auctions()
    check_auctions_about_to_end()
    auction = get_object_or_404(Auction, slug=slug)
    user = request.user
    
    # a comment was sent to the owner, create a comment object and save it
    if request.method == 'POST':

        if auction.author == user:
            messages.error(request, "You cannot message your own product!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        message_details = request.POST.get("message_details")
        message = Message.objects.filter(auction=auction, sender=request.user, recipient=auction.author).last()
        if not message:
            message = Message.objects.create(auction=auction, sender=request.user, recipient=auction.author)
        MessageDetails.objects.create(
                message=message,
                message_details=message_details,
                senderdetails=message.sender,
                recipientdetails=message.recipient
            )
        message.recipient_read = False
        message.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    bids_amount = Bidder.objects.filter(auction=auction).count()

    # Pass the auction title to the context
    nextBidprice = 0
    if auction.type == 'auction' or auction.type == 'auction & buy-it-now':
        nextBidprice = auction.price + auction.bid_increments
    auction_title = auction.title
    auction_id = auction.id
    comments = Comment.objects.filter(auction=auction_id, user=user).order_by('created_at')


    reviews = Review.objects.filter(product=auction).order_by("-created_at")
    average = reviews.aggregate(Avg("rate"))["rate__avg"]
    if average == None:
        average=0
    else:
        average = round(average,2)
    reverse = 'Reverse Not Met!'
    if auction.reserve_price <= auction.price:
        reverse = 'Reverse Met!'
    context = {
        'bids_amount': bids_amount,
        'nextBidprice': nextBidprice,
        'auction': auction, 
        'auction_title': auction_title, 
        'auction_id': auction_id, 
        'comments': comments,
        'reviews':reviews,
		'average':average,
        'reverse': reverse
        }
    return render(request, 'auctions/details.html', context)


@profile_complete_required
def auctions_submit(request):
    check_expired_auctions()
    if request.method == 'POST':
        user = request.user
        bid_price = request.POST.get('bid_price')
        auction_id = request.POST.get('auction_id')
        auction = Auction.objects.filter(id=auction_id)
        # already_bid = Bidder.objects.filter(user=user, auction=auction[0])

        if float(bid_price) is False:
            messages.error(request, "Price must be in float numbers!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if auction[0].author == user:
            messages.error(request, "You cannot Bid your own auction!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # if already_bid:
        #     messages.error(request, f"You already Bid this auction!")
        #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if timezone.now() < auction[0].expired_date:
            if auction[0].quantity > 0:
                if (auction[0].price + auction[0].bid_increments) <= float(bid_price):
                    bid = Bidder(auction=auction[0], user=user, bid_amount=bid_price, type='auction')
                    bid.save()

                    # Update the specific field
                    auction_bid = get_object_or_404(Auction, id=auction_id)
                    auction_bid.price = bid_price
                    auction_bid.amount_of_bids = auction_bid.amount_of_bids + 1
                    auction_bid.save()
                    messages.success(request, f"Successfully Submit the Auction!")

                    if float(bid_price) == float(auction_bid.direct_buy):
                        bid.winningBid = True
                        bid.save()
                        auction_bid.quantity = auction_bid.quantity - 1
                        auction_bid.winnerBid = bid
                        auction_bid.save()
                        messages.success(request, f"You won the Auction! A mail has been set to you soon!")

                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                messages.error(request, f"Bid price must be more than the Minimum Bid! Your Bid is ${bid_price}.")
            else:
                messages.error(request, f"Quantity has achieved its end!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, f"Auction has ended.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



def auctions_submit_ajax(request):
    check_expired_auctions()
    if request.method == 'POST':
        user = request.user
        bid_price = request.POST.get('bid_price')
        auction_id = request.POST.get('auction_id')
        auction = Auction.objects.filter(id=auction_id)

        if float(bid_price) is False:
            return JsonResponse({'success': False, 'message': 'Price must be in float numbers!'})

        if auction[0].author == user:
            return JsonResponse({'success': False, 'message': 'You cannot Bid your own auction!'})

        if timezone.now() >= auction[0].expired_date:
            return JsonResponse({'success': False, 'message': 'Auction has ended.'})

        if auction[0].quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity has achieved its end!'})

        if (auction[0].price + auction[0].bid_increments) > float(bid_price):
            return JsonResponse({'success': False, 'message': f'Bid price must be more than the Minimum Bid! Your Bid is ${bid_price}.'})

        bid = Bidder(auction=auction[0], user=user, bid_amount=bid_price, type='auction')
        bid.save()

        auction_bid = Auction.objects.get(id=auction_id)
        auction_bid.price = bid_price
        auction_bid.amount_of_bids += 1
        auction_bid.save()

        reverse = 'Reverse Not Met!'
        if auction[0].reserve_price <= auction[0].price:
            reverse = 'Reverse Met!'
        

        bids_amount = Bidder.objects.filter(auction=auction[0]).count()
        nextBidprice = 0
        if auction[0].type == 'auction' or auction[0].type == 'auction & buy-it-now':
            nextBidprice = auction[0].price + auction[0].bid_increments

        if float(bid_price) == float(auction_bid.direct_buy):
            bid.winningBid = True
            bid.save()
            auction_bid.quantity -= 1
            auction_bid.winnerBid = bid
            auction_bid.save()
            return JsonResponse({
                'success': True, 
                'message': 'Successfully submitted the Auction!', 
                'auction_price': auction_bid.price,
                'nextBidprice': nextBidprice,
                'bids_amount': bids_amount,
                'reverse': reverse
                })
        else:
            return JsonResponse({
                'success': True, 
                'message': 'Successfully submitted the Auction!', 
                'auction_price': auction_bid.price, 
                'nextBidprice': nextBidprice,
                'bids_amount': bids_amount,
                'reverse': reverse
                })

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def auctions_bid_details(request, slug):
    check_expired_auctions()
    auction = get_object_or_404(Auction, slug=slug)
    bids = Bidder.objects.filter(auction=auction).order_by('bid_amount')

    paginator = Paginator(bids, 30) # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'auction': auction,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }
    return render(request, 'auctions/bid-details.html', context)


# calculating how to increment prices on bids i.e 10 => increase by 1, 100 => increase by 10 etc
def getPercents(auction):
    percents = "1"
    increment = len(str(auction.price)) - 1
    for a in range(increment-1):
        percents = percents + "0"
    percents = int(percents)
    return percents

@login_required
def auctions_mybids(request):
    check_expired_auctions()
    user = request.user
    mybids = Bidder.objects.filter(user=user, type='auction').order_by('-created_at')

    paginator = Paginator(mybids, 10) # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'auctions/auctions/index.html', context)

def auction_mybid_delete(request, id):
    try:
        mybid = Bidder.objects.get(id=id)
        mybid.delete()
    except mybid.DoesNotExist:
        raise Http404("My Bid does not exist")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def auctions_mybids_details(request, slug):
    auction = get_object_or_404(Auction, slug=slug)
    user = request.user
    mybids = Bidder.objects.filter(auction=auction, user=user)
    context = {
        'mybids': mybids,
        'auction': auction
        }
    # return HttpResponse(mybids.auction.slug)
    return render(request, 'auctions/auctions/details.html', context)


def winning_bids(request):
    check_expired_auctions()
    # Pass all auctions that I won here...
    # First find all those that are closed
    # auctions = Auction.objects.filter(closed=True, type='auction')
    # # Now find the winningBid is equal to me
    # myWins = []
    # for aucs in auctions:
    #     # Are there any winning bids on this auction?
    #     if aucs.winnerBid:
    #         # Am i the winning bid?
    #         if aucs.winnerBid.user == request.user:
    #             myWins.append(aucs)

    myWins = Bidder.objects.filter(winningBid=True, user=request.user).order_by('-created_at')

    paginator = Paginator(myWins, 10) # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'auctions/auctions/winner.html', context)


def closedAuctions(request):
    check_expired_auctions()
    items = Auction.objects.filter(closed=True).order_by('-id')

    paginator = Paginator(items, 10) # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'auctions/auctions/closed.html', context)


def auctions_vendor_list(request, author):
    items = Auction.objects.filter(closed=False, author__username=author)

    paginator = Paginator(items, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author': author,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'auctions/auctions/vendor/index.html', context)


def auction_invoice(request, slug):
    product = get_object_or_404(Auction, slug=slug)
    userdetails = UserProfile.objects.get(username=request.user)
    delivery_fee = DeliveryCharge.objects.filter(status=True).last()
    billing = BillingAddress.objects.filter(user=userdetails).last()
    order = Order.objects.filter(user=userdetails, auction=product, product_type='auction').last()
    invoice = Invoice.objects.filter(user=userdetails, order=order).last()

    if delivery_fee is None:
        delivery_fee_total = 0
    else:
        delivery_fee_total = delivery_fee.delivery_fee

    with transaction.atomic():
        if not billing:
            billing = BillingAddress.objects.create(
                user=userdetails, 
                email=userdetails.email, 
                first_name = userdetails.first_name,
                last_name = userdetails.last_name,
                address = userdetails.address,
                state = userdetails.state,
                city = userdetails.city,
                street = userdetails.street,
                house = userdetails.house,
                zip_code = userdetails.zip_code,
                postal_code = userdetails.postal_code,
                phone = userdetails.phone
            )

        if not order:
            order = Order.objects.create(
                auction=product,
                product_type='auction', 
                user=userdetails, 
                billing=billing, 
                quantity=1, 
                paid_amount=product.price + delivery_fee_total,
                balance_type='debit',
                paid=True
            )
        
        if not invoice:
            invoice = Invoice.objects.create(user=userdetails, order=order)

    context = {
        'invoice': invoice,
        'delivery_fee': delivery_fee,
        'total': invoice.order.paid_amount + delivery_fee_total
    }
    return render(request, 'payment/success-order.html', context)


def buy_it_now(request, slug):
    userdetails = UserProfile.objects.get(username=request.user)
    product = get_object_or_404(Auction, slug=slug)
    delivery_fee = DeliveryCharge.objects.filter(status=True).last()
    billing_profile = BillingAddress.objects.filter(user=userdetails).last()
    shipping_profile = ShippingAddress.objects.filter(user=userdetails).last()
    percentage = PercentageGain.objects.filter(status=True).last()

    # Find Percentage Of the Product
    percentage_price = round(product.direct_buy * (percentage.percentage / 100), 2)


    if delivery_fee is None:
        delivery_fee_total = 0
    else:
        delivery_fee_total = delivery_fee.delivery_fee

    if request.method == 'POST':
        if billing_profile:
            billing_form = BillingAddressForm(request.POST, prefix='billing', instance=billing_profile)
            shipping_form = ShippingAddressForm(request.POST, prefix='shipping', instance=shipping_profile)
        else:
            billing_form = BillingAddressForm(request.POST, prefix='billing')
            shipping_form = ShippingAddressForm(request.POST, prefix='shipping')

        with transaction.atomic():
            if billing_form.is_valid():
                billing = billing_form.save(commit=False)
                billing.user = userdetails
                billing.same_as_shipping = True
                billing.save()

                billing_profile = BillingAddress.objects.filter(user=userdetails).last()
                context = {
                    'product': product,
                    'userdetails': userdetails,
                    'billing_profile': billing_profile,
                    'delivery_fee': delivery_fee,
                    'percentage_price': percentage_price,
                    'percentage': percentage,
                    'total': product.direct_buy + delivery_fee_total + percentage_price,
                    'type': 'direct_buy'
                }

                same_as_shipping = request.POST.get('same_as_shipping')
                if same_as_shipping == None:
                    if shipping_form.is_valid():
                        shipping = shipping_form.save(commit=False)
                        shipping.user = userdetails
                        shipping.billing = billing
                        shipping.save()
                        billing.same_as_shipping = False
                        billing.save()

                        # Redirect to payment page
                        return render(request, 'payment/payment.html', context)
                elif same_as_shipping == 'on':
                    billing.same_as_shipping = True
                    billing.save()
                    if shipping_profile:
                        shipping_profile.delete()
                    # Redirect to payment page
                    return render(request, 'payment/payment.html', context)

    else:
        if billing_profile:
            billing_form = BillingAddressForm(prefix='billing', instance=billing_profile)
            shipping_form = ShippingAddressForm(prefix='shipping', instance=shipping_profile)
        else:
            billing_form = BillingAddressForm(prefix='billing')
            shipping_form = ShippingAddressForm(prefix='shipping')

    context = {
        'product': product,
        'userdetails': userdetails,
        'billing_profile': billing_profile,
        'billing_form': billing_form,
        'shipping_form': shipping_form,
        'delivery_fee': delivery_fee,
        'percentage': percentage,
        'percentage_price': percentage_price,
        'total': product.direct_buy + delivery_fee_total + percentage_price,
        'type': 'direct_buy'
    }

    return render(request, 'buy-it-now/buy-it-now.html', context)


def confirm_order(request, slug):
    product = get_object_or_404(Auction, slug=slug)
    userdetails = UserProfile.objects.get(username=request.user)
    paymentMethod = request.POST.get('paymentMethod')
    paid_amount = request.POST.get('paid_amount')
    billing_profile = request.POST.get('billing_profile')
    billing = get_object_or_404(BillingAddress, pk=billing_profile)

    same = Order.objects.filter(user=userdetails, auction=product)
    if same:
        messages.error(request, "You already ordered this product!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if request.method == 'POST':
        with transaction.atomic():
            order = Order.objects.create(
                auction=product,
                product_type='direct_buy', 
                user=userdetails, 
                billing=billing, 
                payment_method=paymentMethod, 
                quantity=1, 
                paid_amount=paid_amount,
                balance_type='debit',
                )
            invoice = Invoice.objects.create(user=userdetails, order=order)
            bid = Bidder(auction=product, user=userdetails, bid_amount=paid_amount, type='buy-it-now')
            bid.save()

            product.quantity = product.quantity - 1
            product.winnerBid = bid
            product.closed = True
            product.status = False
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

    # Construct the URL with the query parameter
    url = reverse('success-order') + '?value=' + str(invoice.invoice_no)

    return redirect(url)


def auction_billing(request, slug):
    userdetails = UserProfile.objects.get(username=request.user)
    product = get_object_or_404(Auction, slug=slug)
    delivery_fee = DeliveryCharge.objects.filter(status=True).last()
    billing_profile = BillingAddress.objects.filter(user=userdetails).last()
    shipping_profile = ShippingAddress.objects.filter(user=userdetails).last()
    percentage = PercentageGain.objects.filter(status=True).last()

    # Find Percentage Of the Product
    percentage_price = round(product.price * (percentage.percentage / 100), 2)


    if delivery_fee is None:
        delivery_fee_total = 0
    else:
        delivery_fee_total = delivery_fee.delivery_fee

    if request.method == 'POST':
        if billing_profile:
            billing_form = BillingAddressForm(request.POST, prefix='billing', instance=billing_profile)
            shipping_form = ShippingAddressForm(request.POST, prefix='shipping', instance=shipping_profile)
        else:
            billing_form = BillingAddressForm(request.POST, prefix='billing')
            shipping_form = ShippingAddressForm(request.POST, prefix='shipping')

        with transaction.atomic():
            if billing_form.is_valid():
                billing = billing_form.save(commit=False)
                billing.user = userdetails
                billing.same_as_shipping = True
                billing.save()

                billing_profile = BillingAddress.objects.filter(user=userdetails).last()
                context = {
                    'product': product,
                    'userdetails': userdetails,
                    'billing_profile': billing_profile,
                    'delivery_fee': delivery_fee,
                    'percentage_price': percentage_price,
                    'percentage': percentage,
                    'total': product.price + delivery_fee_total + percentage_price,
                    'type': 'auction'
                }

                same_as_shipping = request.POST.get('same_as_shipping')
                if same_as_shipping == None:
                    if shipping_form.is_valid():
                        shipping = shipping_form.save(commit=False)
                        shipping.user = userdetails
                        shipping.billing = billing
                        shipping.save()
                        billing.same_as_shipping = False
                        billing.save()

                        # Redirect to payment page
                        return render(request, 'payment/payment.html', context)
                elif same_as_shipping == 'on':
                    billing.same_as_shipping = True
                    billing.save()
                    if shipping_profile:
                        shipping_profile.delete()
                    # Redirect to payment page
                    return render(request, 'payment/payment.html', context)

    else:
        if billing_profile:
            billing_form = BillingAddressForm(prefix='billing', instance=billing_profile)
            shipping_form = ShippingAddressForm(prefix='shipping', instance=shipping_profile)
        else:
            billing_form = BillingAddressForm(prefix='billing')
            shipping_form = ShippingAddressForm(prefix='shipping')

    context = {
        'product': product,
        'userdetails': userdetails,
        'billing_profile': billing_profile,
        'billing_form': billing_form,
        'shipping_form': shipping_form,
        'delivery_fee': delivery_fee,
        'percentage': percentage,
        'percentage_price': percentage_price,
        'total': product.price + delivery_fee_total + percentage_price,
        'type': 'auction'
    }

    return render(request, 'buy-it-now/auction-billing.html', context)


def success_order(request):
    value = request.GET.get('value')
    invoice = Invoice.objects.filter(invoice_no=value).last()
    delivery_fee = DeliveryCharge.objects.filter(status=True).last()
    percentage = PercentageGain.objects.filter(status=True).last()

    type = invoice.order.product_type
    if type == 'direct_buy':
        price = invoice.order.auction.direct_buy
        # Find Percentage Of the Product
        percentage_price = round(invoice.order.auction.direct_buy * (percentage.percentage / 100), 2)
    else:
        price = invoice.order.auction.price
        # Find Percentage Of the Product
        percentage_price = round(invoice.order.auction.price * (percentage.percentage / 100), 2)

    context = {
        'invoice': invoice,
        'price': price,
        'percentage': percentage,
        'percentage_price': percentage_price,
        'delivery_fee': delivery_fee,
        'total': invoice.order.paid_amount
    }
    return render(request, 'payment/success-order.html', context)


def my_orders(request):
    my_orders = Invoice.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(my_orders, 10) # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }

    return render(request, 'dashboard/_preview/_order.html', context)


def searching(request):
    if request.method == 'GET':
        query = request.GET.get('query')
        results = Auction.objects.filter(Q(title__icontains=query) | Q(condition__icontains=query), closed=False)

        context = {
            'results': results, 
            'query': query
        }
        
    return render(request, 'search_results.html', context)


def export_invoice(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    delivery_fee = DeliveryCharge.objects.filter(status=True).last()
    percentage = PercentageGain.objects.filter(status=True).last()

    price = invoice.order.auction.direct_buy
    # Find Percentage Of the Product
    percentage_price = round(invoice.order.auction.direct_buy * (percentage.percentage / 100), 2)

    if delivery_fee is None:
        delivery_fee_total = 0
    else:
        delivery_fee_total = delivery_fee.delivery_fee
    
    context = {
        'invoice': invoice,
        'price': price,
        'percentage': percentage,
        'percentage_price': percentage_price,
        'delivery_fee': delivery_fee,
        'total': invoice.order.paid_amount + delivery_fee_total
    }

    return render(request, 'auctions/invoice.html', context)
    
    # # Get the template
    # template_path = 'auctions/invoice.html'  # Replace 'your_template.html' with your template path
    # template = get_template(template_path)

    # # Render the template with context data
    # context = {
    #     'invoice': invoice,
    #     'delivery_fee': delivery_fee,
    #     'total': invoice.order.paid_amount + delivery_fee.delivery_fee
    #     }  # Add context data if needed
    # html = template.render(context)

    # # Create a PDF response
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename="output.pdf"'

    # # Generate PDF
    # pisa_status = pisa.CreatePDF(html, dest=response)
    # if pisa_status.err:
    #     return HttpResponse('Failed to generate PDF: {}'.format(pisa_status.err))

    # return response


def reports(request):
    queryset = 0
    total_sales = 0
    query = request.GET.get('query')

    # Define date ranges for daily, weekly, monthly, and yearly reports
    today = datetime.now()

    # Create a new datetime object for today at 00:00 (midnight)
    today_midnight = datetime(today.year, today.month, today.day)
    one_week_ago = today - timedelta(weeks=1)
    one_month_ago = today - timedelta(days=30)
    one_year_ago = today - timedelta(days=365)

    if request.method == 'GET':
        if query == 'daily':
            queryset = Transaction.objects.filter(author=request.user, balance_type='debit', created_at__gte=today_midnight, created_at__lte=today)
        elif query == 'weekly':
            queryset = Transaction.objects.filter(created_at__gte=one_week_ago, created_at__lte=today, balance_type='debit', author=request.user)
        elif query == 'monthly':
            queryset = Transaction.objects.filter(created_at__gte=one_month_ago, created_at__lte=today, balance_type='debit', author=request.user)
        elif query == 'yearly':
            queryset = Transaction.objects.filter(created_at__gte=one_year_ago, created_at__lte=today, balance_type='debit', author=request.user)
        else:
            queryset = Transaction.objects.filter(author=request.user, balance_type='debit', created_at__gte=today_midnight, created_at__lte=today)
        
        total_sales = queryset.aggregate(total_sales=Sum('price'))['total_sales'] or 0

    context = {
        'total_sales': total_sales,
        'queryset': queryset,
        'query': query
    }

    return render(request, 'reports.html', context)


@login_required
def rating(request, id):
    product = Auction.objects.get(id=id)
    if request.method == "POST":
        form = ReviewForm(request.POST or None)
        if form.is_valid():
            data = form.save(commit=False)
            data.comment = request.POST["comment"]
            data.rate = request.POST["rate"]
            data.user = request.user
            data.product = product
            data.save()
            messages.success(request, f"Rating Successfully Submitted!")
        else:
            messages.error(request, f"Something Went Wrong!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# This gets called whenever we want to check the auctions if theyre closed or finished etc..
def check_expired_auctions():
    expired_auctions = Auction.objects.filter(expired_date__lte=timezone.now(), closed=False)
    bids = Bidder.objects.all()

    for auc in expired_auctions:
        if auc.expired and auc.closed == False:
            auc.closed = True
            auc.status = False

            # Set the last bid on here to maxed out and save it into auction
            last_bid = bids.filter(auction=auc).last()
            if last_bid and auc.reserve_price is not None:
                if float(last_bid.bid_amount) >= float(auc.reserve_price):
                    if auc.winnerBid is None:
                        auc.quantity = auc.quantity - 1
                        auc.winnerBid = last_bid
                        last_bid.winningBid = True
                        last_bid.save()
                else:
                    auc.winnerBid = None
                    auc.save()
            auc.save()
            alreday_exists = Notification.objects.filter(mail_sent=True)
            for item in alreday_exists:
                item.mail_sent = False
                item.save()

            if last_bid:
                subject = 'Won auction - ' + str(auc.title)
                message = 'Congratulations on winning the auction titled ' + str(auc.title) + " please pay the user " + str(auc.author.username) + ", the sum of £" + str(auc.price) + "."
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [last_bid.user.email,]

                try:
                    send_mail(subject, message, email_from, recipient_list)
                except:
                    pass


# Inside a function to check auctions that are about to end
def check_auctions_about_to_end():
    msg = NotificationMessage.objects.filter(status=True).last()

    if msg is None:
        print("Error: No active NotificationMessage found.")
        return

    try:
        threshold_time = timezone.now() + timezone.timedelta(hours=msg.hour_before)
    except AttributeError as e:
        print(f"AttributeError: {e}")
        return

    ending_auctions = Auction.objects.filter(
        expired_date__lte=threshold_time,
        type__in=['auction', 'auction & buy-it-now'],
        closed=False
    )

    for auction in ending_auctions:
        # Create notifications for bidders
        bidders = Bidder.objects.filter(type='auction').values_list('user', flat=True).distinct()
        for bidder in bidders:
            userprofile = UserProfile.objects.filter(id=bidder).last()
            already_exists = Notification.objects.filter(user=userprofile, mail_sent=True).last()

            message_content = f"Hello Sir,\n{msg.message}\nAuction Title: {auction.title}"

            if already_exists is None:
                notification = Notification.objects.create(
                    auction=auction,
                    user=userprofile,
                    message=message_content
                )
                if notification:
                    subject = msg.subject
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [userprofile.email]

                    try:
                        send_mail(subject, message_content, email_from, recipient_list)
                        notification.mail_sent = True
                        notification.save()
                    except Exception as e:
                        print(f"Failed to send email: {e}")

def notification_details(request, id):
    notification = Notification.objects.get(id=id)
    notification.is_read = True
    notification.save()
    context = {
        'notification' : notification
    }
    return render(request, 'notification-details.html', context)

