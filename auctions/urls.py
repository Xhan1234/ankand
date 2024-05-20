from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views


urlpatterns = [
    path('auctions/', views.auctions, name='auctions'),
    path('auction-add', views.auction_add, name='auction-add'),
    path('auction/edit/<str:slug>', views.auction_edit, name='auction-edit'),
    path('auction-details/<str:slug>/', views.auction_details, name='auction-details'),
    path('auction/delete/<str:slug>', views.auction_delete, name='auction-delete'),

    # Auctions
    path('auctions-submit' , views.auctions_submit, name='auctions-submit'),
    path('auctions-submit-ajax' , views.auctions_submit_ajax, name='auctions-submit-ajax'),
    path('auctions/bid/<str:slug>', views.auctions_bid_details, name='auction-bid-details'),
    path('auctions-mybids/' , views.auctions_mybids, name='auctions-mybids'),
    path('auction-my-bid-delete/<int:id>' , views.auction_mybid_delete, name='auction-my-bid-delete'),
    path('auctions-mybids/details/<str:slug>' , views.auctions_mybids_details, name='auctions-mybids-details'),
    path('auctions-winning', views.winning_bids, name='auctions-winning'),
    path('auctions-closed', views.closedAuctions, name='auction-closed'),

    # Auction Vendor Product List
    path('auctions/vendor/<str:author>', views.auctions_vendor_list, name='auctions-vendor'),

    # Direct Buy
    path('buy-it-now/<str:slug>', views.buy_it_now, name='buy-it-now'),
    path('confirm/order/<str:slug>', views.confirm_order, name='confirm-order'),
    path('success/order', views.success_order, name='success-order'),
    path('auction-billing/<str:slug>', views.auction_billing, name='auction-billing'),
    path('export-invoice/<int:invoice_id>/', views.export_invoice, name='export-invoice'),

    # My Orders
    path('my-orders/' , views.my_orders, name='my-orders'),

    # Search
    path('search' , views.searching, name='search'),

    # Invoice
    path('auction-invoice/<str:slug>', views.auction_invoice, name='auction-invoice'),

    path('rating/<str:id>', views.rating, name='rating'),

    path('notification-details/<str:id>', views.notification_details, name='notification-details'),

    path('reports' , views.reports, name='reports'),

    ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)