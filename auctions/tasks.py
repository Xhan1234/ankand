# tasks.py

from celery import shared_task
from .models import Auction, Bidder
from django.utils import timezone

@shared_task
def check_expired_auctions():
    expired_auctions = Auction.objects.filter(expired_date__lte=timezone.now(), closed=False)
    bids = Bidder.objects.all()

    for auc in expired_auctions:
        if auc.expired and auc.closed == False:
            auc.closed = True
            auc.status = False

            # Set the last bid on here to maxed out and save it into auction
            last_bid = bids.filter(auction=auc).last()
            if last_bid is not None:
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
