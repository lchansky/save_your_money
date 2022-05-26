from django.urls import path, include
from .views import *

urlpatterns = [
    path('', HomeOperations.as_view(), name='home'),
    path('operations/', HomeOperations.as_view(), name='operations'),
    path('operations/new/', operation_new, name='operation_new'),
    path('operations/<int:pk>', OperationDetail.as_view(), name='operation_detail'),
    path('operations/delete/<int:pk>', operation_delete, name='operation_delete'),
    path('operations/edit/<int:pk>', operation_edit, name='operation_edit'),
    
    path('wallets/', Wallets.as_view(), name='wallets'),
    path('wallets/<int:pk>', WalletDetail.as_view(), name='wallet_detail'),
    path('wallets/delete/<int:pk>', wallet_delete, name='wallet_delete'),
    
    path('categories/', Categories.as_view(), name='categories'),
    
    path('settings/', Settings.as_view(), name='settings'),
    path('settings/<success>/', Settings.as_view(), name='settings'),
    
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    path('about/', about, name='about'),
]
