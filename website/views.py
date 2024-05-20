from auctions.models import Auction, Category
from django.shortcuts import render
from users.models import UserProfile
from django.core.paginator import Paginator
from website.models import *
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.http import HttpResponseRedirect
from auctions.views import check_expired_auctions, check_auctions_about_to_end


def home(request):
    check_expired_auctions()
    check_auctions_about_to_end()
    sliders = Slider.objects.filter(status=True).order_by('-id')
    category = Category.objects.filter(status=True).order_by('-id')
    auctions = Auction.objects.filter(closed=False).order_by('-id')[:12] #, quantity__gt=0
    context = {
        'auctions': auctions,
        'sliders': sliders,
        'category': category
        }
    return render(request, 'index.html', context)

def live_auctions_list(request):
    check_expired_auctions()
    check_auctions_about_to_end()
    auctions = Auction.objects.filter(closed=False).order_by('-id')

    paginator = Paginator(auctions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }
    return render(request, 'live-auctions-list.html', context)


def category(request, slug):
    check_expired_auctions()
    check_auctions_about_to_end()
    category = get_object_or_404(Category, slug=slug)
    auctions = Auction.objects.filter(closed=False, category=category)
    categories = Category.objects.filter(status=True).order_by('-id')

    paginator = Paginator(auctions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1
    }
    return render(request, 'category-auctions.html', context)


def about(request):
    return render(request, 'about.html')


def blog(request):
    return render(request, 'blog.html')


def blog_details(request):
    return render(request, 'blog-details.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        Contact.objects.create(name=name, email=email, phone=phone, subject=subject, message=message)
        messages.success(request, f"Message Sent Successfully. Thank You!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return render(request, 'contact.html')


def inbox(request):
    return render(request, 'inbox.html')

def store_listing(request):
    vendors = UserProfile.objects.filter(role='vendor')
    vendor_count = vendors.count()
    return render(request, 'temp-files/store-listing/index.html', {'vendors': vendors, 'vendor_count': vendor_count})


def shop(request):
    auctions = Auction.objects.all()
    return render(request, 'temp-files/shop/index.html', {'auctions': auctions})

def blog_grid(request):
    return render(request, 'temp-files/blog-grid/index.html')


def blog_standard(request):
    return render(request, 'temp-files/blog-standard/index.html')

def blog_standard1(request):
    return render(request, 'temp-files/blog-standard/page/2/index.html')


def accessories(request):
    return render(request, 'temp-files/auction-category/accessories/index.html')


def antiques(request):
    return render(request, 'temp-files/auction-category/antiques/index.html')


def cars(request):
    return render(request, 'temp-files/auction-category/cars/index.html')


def electronics(request):
    return render(request, 'temp-files/auction-category/electronics/index.html')


def fashion(request):
    return render(request, 'temp-files/auction-category/fashion/index.html')


def music(request):
    return render(request, 'temp-files/auction-category/music/index.html')


def trading_card(request):
    return render(request, 'temp-files/auction-category/trading-card/index.html')



def vehicles(request):
    return render(request, 'temp-files/auction-category/vehicles/index.html')



def virtual_worlds(request):
    return render(request, 'temp-files/auction-category/virtual_worlds/index.html')



def watches(request):
    return render(request, 'temp-files/auction-category/watches/index.html')


def how_it_works(request):
    return render(request, 'temp-files/how-it-works/index.html')


def alarm_clock_1990s(request):
    return render(request, 'temp-files/auction/alarm-clock-1990s/index.html')


def black_analogue_watch(request):
    return render(request, 'temp-files/auction/black-analogue-watch/index.html')


def brand_new_honda_cbr_600_special_sale_2022(request):
    return render(request, 'temp-files/auction/brand-new-honda-cbr-600-special-sale-2022/index.html')


def creative_fashion_ribbon_digital_sun_class_s22(request):
    return render(request, 'temp-files/auction/creative-fashion-ribbon-digital-sun-class-s22/index.html')


def ford_shelby_white_car(request):
    return render(request, 'temp-files/auction/ford-shelby-white-car/index.html')


def havit_hv_g61_usb_black_double_game_vibrat(request):
    return render(request, 'temp-files/auction/havit_hv_g61_usb_black_double_game_vibrat/index.html')


def iphone_11_pro_max_available_for_special_sale(request):
    return render(request, 'temp-files/auction/iphone-11-pro-max-available-for-special-sale/index.html')


def leather_digital_watch(request):
    return render(request, 'temp-files/auction/leather-digital-watch/index.html')


def macbook_pro_2018(request):
    return render(request, 'temp-files/auction/macbook-pro-2018/index.html')


def premium_1998_typewriter(request):
    return render(request, 'temp-files/auction/premium-1998-typewriter/index.html')


def red_color_special_lighter_2_2_for_saleing_offer(request):
    return render(request, 'temp-files/auction/red-color-special-lighter-2-2-for-saleing-offer/index.html')


def stylish_digital_airpods(request):
    return render(request, 'temp-files/auction/stylish-digital-airpods/index.html')


def toyota_aigid_a_class_hatchback_2017_2021(request):
    return render(request, 'temp-files/auction/toyota-aigid-a-class-hatchback-2017-2021/index.html')


def wedding_couple_ring(request):
    return render(request, 'temp-files/auction/wedding-couple-ring/index.html')


def a_brand_for_a_company_is_like_for_a_person(request):
    return render(request, 'temp-files/a-brand-for-a-company-is-like-for-a-person/index.html')


def faq(request):
    return render(request, 'temp-files/faq/index.html')


def not_found(request):
    return render(request, 'temp-files/404.html')


def wishlist(request):
    return render(request, 'temp-files/wishlist/index.html')


def david_droga_still_has_faith_in_online_creative_copy_copy(request):
    return render(request, 'temp-files/david-droga-still-has-faith-in-online-creative-copy-copy/index.html')


def david_droga_still_has_faith_in_online_creative_copy(request):
    return render(request, 'temp-files/david-droga-still-has-faith-in-online-creative-copy/index.html')


def david_droga_still_has_faith_in_online_creative(request):
    return render(request, 'temp-files/david-droga-still-has-faith-in-online-creative/index.html')


def a_brand_for_a_company_is_like_for_a_person(request):
    return render(request, 'temp-files/a-brand-for-a-company-is-like-for-a-person/index.html')


def auctionivity_strategies_backed_by_science(request):
    return render(request, 'temp-files/10-auctionivity-strategies-backed-by-science/index.html')


def lost_password(request):
    return render(request, 'temp-files/register/lost-password/index.html')
