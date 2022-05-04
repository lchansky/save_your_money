from django.shortcuts import render, redirect
from django.http import HttpResponse, request
from django.views.generic import ListView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

from .models import *


# def auth_redirect(func):
#     if request.user.is_authenticated():
#         return redirect('home')
#     else:
#         return func


def about(request):
    print(request)
    return render(request, 'base.html')


# @auth_redirect
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('login')
        else:
            messages.error(request, 'Ошибка регистрации')
    else:
        form = UserCreationForm()
    return render(request, 'sym_app/register.html', {'form': form})


def login(request):
    return render(request, 'sym_app/login.html')


class HomeOperations(ListView):
    model = Currency
    template_name = 'sym_app/home_operations.html'
    
    context_object_name = 'currencies'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список операций'
        return context
    