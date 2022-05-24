import datetime
from pprint import pprint

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import request
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import ListView, CreateView, UpdateView, FormView, DetailView
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model, get_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F

from .models import *
from .forms import UserRegisterForm, UserLoginForm, OperationNewForm, forms, UserSettingsForm


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
        context['operations_in_days'] = self.get_operations_in_days()
        # context['sorting'] = self.sorting()
        context.update(universal_context(self.request))
        print(self.sorting())
        return context
    
    def get_operations_in_days(self):
        operations = self.get_queryset()
        operations_in_days = {}  # {date1: [operation1, operation2, ...], date2: [operation3, operation4, ...], }
        
        days = set()  # Создаём множество из уникальных дат
        for operation in operations:
            days.add(operation.updated_at.date())
        days = list(days)
        days.sort(reverse=True)
        
        for day in days:  # Образуем словарь, где ключ - это дата, а значение - список из операций с этой датой
            operations_in_days[day] = list()
            for operation in operations:
                if operation.updated_at.date() == day:
                    operations_in_days[day].append(operation)
        
        return operations_in_days
    
    def sorting(self):
        kwargs = {}
        kwargs['user'] = self.request.user
        kwargs['category__type_of'] = self.request.GET.get("type_of", F('category__type_of'))
        q = Q(user=kwargs['user']) & Q(category__type_of=kwargs['category__type_of'])
        
        kwargs['from_wallet__pk'] = self.request.GET.get("wallet", F('from_wallet__pk'))
        kwargs['to_wallet__pk'] = self.request.GET.get("wallet", F('to_wallet__pk'))
        q = q & (Q(from_wallet__pk=kwargs['from_wallet__pk']) | Q(to_wallet__pk=kwargs['to_wallet__pk']))
        return q
    
    def get_queryset(self):
        return Operation.objects.filter(self.sorting())
        

@login_required(login_url='about')
def operation_new(request):
    if request.method == 'POST':
        form = OperationNewForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            if not data['currency2'] or not data['amount2']:
                data['currency2'] = data['currency1']
                data['amount2'] = data['amount1']
            
            operation = Operation.objects.create(**data)
            print('Новая операция:', operation)
            messages.success(request, 'Операция добавлена')
            return redirect('home')
    else:
        form = OperationNewForm(request=request)
    return render(request,
                  'sym_app/operation_new.html',
                  {'form': form,
                   'title': 'Добавление операции',
                   'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
                   'main_currency_id': Currency.objects.get(name='RUB').pk,
                   # Здесь нужно будет в будущём отправить в контекст основную валюту пользователя, а не просто Рубль. Чтобы отображать расходы с разными валютами, в одной - основной валюте
                   }
                  )


def universal_context(request):
    """Принимает запрос и контекст, добавляет к контексту те переменные, которые используются на каждой странице.
    Например, на navbar используется"""
    extra_context = {}
    extra_context['wallets'] = Wallet.objects.filter(user=request.user)
    return extra_context


class Wallets(LoginRequiredMixin, ListView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Wallet
    template_name = 'sym_app/wallets.html'
    context_object_name = 'wallets'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список счетов'
        context.update(universal_context(self.request))
        return context
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)


class Categories(LoginRequiredMixin, ListView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Category
    template_name = 'sym_app/categories.html'
    
    context_object_name = 'categories'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список категорий'
        context['categories_pay'], context['categories_earn'] = self.categories_pay_earn()
        # print(context['categories_pay'])
        context.update(universal_context(self.request))
        return context
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def categories_pay_earn(self):
        """Возвращает 2 списка - список расходных и список доходных категорий пользователя"""
        categories = self.get_queryset()
        categories_pay = Category.objects.filter(user=self.request.user, type_of='pay')
        categories_earn = Category.objects.filter(user=self.request.user, type_of='earn')
        return categories_pay, categories_earn


class Settings(LoginRequiredMixin, UpdateView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Profile
    template_name = 'sym_app/settings.html'
    form_class = UserSettingsForm
    success_url = '__self__'
    context_object_name = 'user_settings'
    
    def form_valid(self, form):
        messages.success(self.request, 'Настройки успешно сохранены')
        return super().form_valid(form)
        
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Настройки'
        context.update(universal_context(self.request))
        return context
    
    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)
