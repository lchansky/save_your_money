from django.urls import path, include
from .views import *

urlpatterns = [
    path('', HomeOperations.as_view(), name='home'),
    path('operations/', operations, name='operations'),
    path('operations/new/', operation_new, name='operation_new'),
    
    
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    path('about/', about, name='about'),
]
