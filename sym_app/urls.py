from django.urls import path, include
from .views import *

urlpatterns = [
    path('', HomeOperations.as_view(), name='home'),
    path('operations/', HomeOperations.as_view(), name='operations'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    path('about/', about, name='about'),
]
