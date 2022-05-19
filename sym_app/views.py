from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import request
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import ListView, CreateView
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model, get_user
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import *
from .forms import UserRegisterForm, UserLoginForm, OperationNewForm


def about(request):
    print(request)
    return render(request, 'sym_app/about.html', {'title': 'О проекте'})


def user_logout(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('home')
        else:
            messages.error(request, 'Ошибка регистрации')
    else:
        form = UserRegisterForm()
    return render(request, 'sym_app/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'sym_app/login.html', {'form': form})


class HomeOperations(LoginRequiredMixin, ListView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Operation
    template_name = 'sym_app/home_operations.html'
    
    context_object_name = 'operations'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список операций'
        return context
    
    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user)
    
    def get_user_operations(self):
        return Operation.objects.filter(user=self.request.user)
    

@login_required(login_url='about')
def operations(request):
    return render(request, 'sym_app/operations.html', {'operations': Operation.objects.filter(user=request.user)})


def form_get_request(form):
    if form.Meta.request:
        return form.Meta.request
    else:
        print('NO REQUEST')


@login_required(login_url='about')
def operation_new(request):
    if request.method == 'POST':
        form = OperationNewForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            if not data['currency2']:
                data['currency2'] = data['currency1']
                data['amount2'] = data['amount1']
            
            operation = Operation.objects.create(**data)
            print('Новая операция:', operation)
            return redirect('operations')
    else:
        form = OperationNewForm(request=request)
    return render(request,
                  'sym_app/operation_new.html',
                  {'form': form,
                   'title': 'Добавление операции',
                   'transfer_category_id': Category.objects.get(user=request.user, type_of='transfer').pk,
                   'main_currency_id': Currency.objects.get(name='RUB').pk,  # Здесь нужно будет в будущём отправить в контекст основную валюту пользователя, а не просто Рубль
                   }
                  )


def operation_new_success(request):
    pass