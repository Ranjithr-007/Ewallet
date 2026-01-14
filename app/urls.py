"""WalletAPI.app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from app import views

urlpatterns = [
    path('register/', views.api_create_account, name='register'),
    path('login/', views.api_login, name='login'),
    
    path('create-wallet/', views.api_create_wallet, name='create-wallet'),
    path('wallet/add/', views.add_money),
    path('wallet/spend/', views.spend_money),
    path('wallet/transfer/', views.transfer_money),
    path('wallet/<str:wallet_id>/transactions/', views.wallet_transactions),
    path('wallet/<str:wallet_id>/summary/', views.wallet_summary, name='wallet_summary'),
    path('wallet/<str:wallet_id>/monthly-report/<int:year>/', views.wallet_monthly_report, name='wallet_monthly_report'),
]
