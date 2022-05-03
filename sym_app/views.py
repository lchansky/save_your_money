from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView

from .models import *


def about(request):
    print(request)
    return render(request, 'sym_app/about.html')


class HomeOperations(ListView):
    model = Currency
    template_name = 'sym_app/home_operations.html'
    
    context_object_name = 'currencies'
    