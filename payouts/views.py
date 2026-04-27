from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

from .models import Merchant, BankAccount, IdempotencyKey
from .services import create_payout, run_worker
from .serializers import PayoutSerializer


class CreatePayoutView(APIView):

    @transaction.atomic
    def post(self, request):
        merchant = Merchant.objects.first()

        key = request.headers.get("Idempotency-Key")

        if not key:
            return Response({"error": "Idempotency-Key required"}, status=400)

        existing = IdempotencyKey.objects.filter(
            merchant=merchant, key=key
        ).first()

        if existing:
            return Response(existing.response_data)

        amount = request.data["amount_paise"]
        bank_account = BankAccount.objects.get(id=request.data["bank_account_id"])
        try:
            payout = create_payout(merchant, amount, bank_account)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        
        data = PayoutSerializer(payout).data

        IdempotencyKey.objects.create(
            merchant=merchant,
            key=key,
            response_data=data,
        )

        # 🔥 simulate async worker
        run_worker()

        return Response(data)