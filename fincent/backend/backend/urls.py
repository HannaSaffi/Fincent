"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# backend/urls.py

# In backend/urls.py or your main urls.py file
from django.urls import include, path
from django.http import HttpResponse

from financeapp import views

def home_view(request):
    return HttpResponse("Welcome to the Finance App!")

urlpatterns = [
    path('', home_view, name='home'),  # Root URL
    path('finance/', include('financeapp.urls')),  # Your finance app URLs
    path('backtest/<str:symbol>/', views.backtest_view, name='backtest'),
]



