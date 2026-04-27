from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
import random

from .models import LedgerEntry, Payout


def get_balance(merchant):
    result = LedgerEntry.objects.filter(merchant=merchant).aggregate(
        credits=Sum("amount_paise", filter=Q(type="credit")),
        debits=Sum("amount_paise", filter=Q(type="debit")),
    )
    return (result["credits"] or 0) - (result["debits"] or 0)


@transaction.atomic
def create_payout(merchant, amount, bank_account):
    LedgerEntry.objects.select_for_update().filter(merchant=merchant)

    balance = get_balance(merchant)

    if balance < amount:
        raise Exception("Insufficient balance")

    payout = Payout.objects.create(
        merchant=merchant,
        amount_paise=amount,
        bank_account=bank_account,
        status="pending",
    )

    LedgerEntry.objects.create(
        merchant=merchant,
        amount_paise=amount,
        type="debit",
    )

    return payout


# 🔥 WORKER LOGIC
@transaction.atomic
def process_payout(payout):
    if payout.status not in ["pending", "processing"]:
        return

    payout.status = "processing"
    payout.attempts += 1
    payout.save()

    r = random.randint(1,100)

    if r <= 70:
        payout.status = "completed"

    elif r <= 90:
        payout.status = "failed"

        # return funds
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            amount_paise=payout.amount_paise,
            type="credit",
        )

    else:
        # hang → retry later
        if payout.attempts >= 3:
            payout.status = "failed"

            LedgerEntry.objects.create(
                merchant=payout.merchant,
                amount_paise=payout.amount_paise,
                type="credit",
            )

        payout.save()
        return

    payout.save()


# simulate background processor
def run_worker():
    payouts = Payout.objects.filter(status__in=["pending", "processing"])
    for p in payouts:
        process_payout(p)