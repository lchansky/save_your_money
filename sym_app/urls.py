from django.urls import path, include
from .views import *

urlpatterns = [
    path('', HomeOperations.as_view(), name='home'),
    path('operations/', HomeOperations.as_view(), name='operations'),
    path('operations/new/', operation_new, name='operation_new'),
    path('operations/<int:pk>', OperationDetail.as_view(), name='operation_detail'),
    path('operations/edit/<int:pk>', operation_edit, name='operation_edit'),
    path('operations/delete/<int:pk>', operation_delete, name='operation_delete'),
    
    path('wallets/', Wallets.as_view(), name='wallets'),
    path('wallets/new/', wallet_new, name='wallet_new'),
    path('wallets/<int:pk>', WalletDetail.as_view(), name='wallet_detail'),
    path('wallets/edit/<int:pk>', wallet_edit, name='wallet_edit'),
    path('wallets/delete/<int:pk>', wallet_delete, name='wallet_delete'),
    
    path('categories/', Categories.as_view(), name='categories'),
    path('categories/new/', category_new, name='category_new'),
    path('categories/<int:pk>', CategoryDetail.as_view(), name='category_detail'),
    path('categories/edit/<int:pk>', category_edit, name='category_edit'),
    path('categories/delete/<int:pk>', category_delete, name='category_delete'),
    
    path('settings/', Settings.as_view(), name='settings'),
    path('settings/<success>/', Settings.as_view(), name='settings'),
    
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    path('about/', about, name='about'),
]
