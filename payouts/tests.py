from django.test import TestCase
from threading import Thread
from .models import Merchant, BankAccount, LedgerEntry
from .services import create_payout


class ConcurrencyTest(TestCase):

    def test_double_payout(self):
        merchant = Merchant.objects.create(name="Test")
        bank = BankAccount.objects.create(merchant=merchant, account_number="123")

        LedgerEntry.objects.create(merchant=merchant, amount_paise=10000, type="credit")

        def attempt():
            try:
                create_payout(merchant, 6000, bank)
            except:
                pass

        t1 = Thread(target=attempt)
        t2 = Thread(target=attempt)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        payouts = merchant.payout_set.count()

        self.assertEqual(payouts, 1)