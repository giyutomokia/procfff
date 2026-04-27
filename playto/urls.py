from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('', lambda request: HttpResponse("Server running")),
    path('api/v1/', include('payouts.urls')),
]