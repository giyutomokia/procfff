from django.urls import path
from .views import CreatePayoutView

urlpatterns = [
    path("payouts", CreatePayoutView.as_view()),
]