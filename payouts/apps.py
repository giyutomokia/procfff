from django.apps import AppConfig


class PayoutsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payouts'

    def ready(self):
        from .models import Merchant, BankAccount, LedgerEntry

        if not Merchant.objects.exists():
            m = Merchant.objects.create(name="Live Merchant")

            bank = BankAccount.objects.create(
                merchant=m,
                account_number="123456789"
            )

            LedgerEntry.objects.create(
                merchant=m,
                amount_paise=10000,
                type="credit"
            )
