import datetime
from pprint import pprint
import pytz
from pytz import UTC

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import ListView, CreateView, UpdateView, FormView, DetailView, DeleteView
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model, get_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F

from sym_django.settings import TIME_ZONE
from .models import *
from .forms import *


def about(request):
    print(request)
    return render(request, 'sym_app/about.html', {'title': 'О проекте'})


def user_logout(request):
    """Деавторизует пользователя. Редирект на home"""
    logout(request)
    return redirect('home')


def register(request):
    """Регистрирует пользователя"""
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
        # print(self.sorting())
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
    

class OperationDetail(LoginRequiredMixin, DetailView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Operation
    template_name = 'sym_app/operation_detail.html'
    context_object_name = 'operation'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(universal_context(self.request))
        context['title'] = 'Детали операции'
        return context
        

@login_required(login_url='about')
def operation_delete(request, pk):
    Operation.objects.get(pk=pk).delete()
    messages.success(request, 'Операция успешно удалена')
    return redirect('home')


@login_required(login_url='about')
def operation_edit(request, pk):
    
    operation = Operation.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = OperationEditForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            if not data['currency2'] or not data['amount2']:
                data['currency2'] = data['currency1']
                data['amount2'] = data['amount1']
            Operation.objects.filter(pk=pk).update(**data)
            print('Изменена операция:', operation)
            messages.success(request, 'Изменения сохранены')
            return redirect(operation.get_absolute_url())
    else:
        # Добавляю дельту таймзоны, т.к. в БД время в UTC.
        dt = operation.updated_at.astimezone(tz=pytz.timezone(TIME_ZONE))
        
        form = OperationEditForm(request=request, initial={
            'updated_at': dt.strftime('%Y-%m-%dT%H:%M'),  # HTML понимает только формат времени 'yyyy-mm-ddThh:mm'
            'from_wallet': operation.from_wallet,
            'category': operation.category,
            'to_wallet': operation.to_wallet,
            'currency1': operation.currency1,
            'amount1': operation.amount1,
            'currency2': operation.currency2,
            'amount2': operation.amount2,
            'description': operation.description,
        })

    context = {'form': form,
               'title': 'Изменение операции',
               'operation': operation,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'main_currency_id': Currency.objects.get(name='RUB').pk,
               # Здесь нужно будет в будущем отправить в контекст основную
               # валюту пользователя, а не просто Рубль. Чтобы отображать
               # расходы с разными валютами, в одной - основной валюте
               }
    context.update(universal_context(request))

    return render(request, 'sym_app/operation_edit.html', context)


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
    
    context = {'form': form,
               'title': 'Добавление операции',
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'main_currency_id': Currency.objects.get(name='RUB').pk,
               # Здесь нужно будет в будущем отправить в контекст основную
               # валюту пользователя, а не просто Рубль. Чтобы отображать
               # расходы с разными валютами, в одной - основной валюте
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/operation_new.html', context)


def universal_context(request):
    """Принимает запрос и контекст, добавляет к контексту те переменные, которые используются на каждой странице.
    Например, на navbar используется"""
    extra_context = {}
    extra_context['optional_name'] = Profile.objects.get(user=request.user).name
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


class WalletDetail(LoginRequiredMixin, DetailView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Wallet
    template_name = 'sym_app/wallet_detail.html'
    context_object_name = 'wallet'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(universal_context(self.request))
        context['title'] = 'Детали счёта'
        return context


@login_required(login_url='about')
def wallet_new(request):
    if request.method == 'POST':
        form = WalletNewForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            
            wallet = Wallet.objects.create(**data)
            print('Новый счёт:', wallet)
            messages.success(request, 'Счёт добавлен')
            return redirect('wallets')
    else:
        form = WalletNewForm()
    
    context = {'form': form,
               'title': 'Добавление счёта',
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/wallet_new.html', context)


@login_required(login_url='about')
def wallet_edit(request, pk):
    wallet = Wallet.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = WalletEditForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            Wallet.objects.filter(pk=pk).update(**data)
            print('Изменён счёт:', wallet)
            messages.success(request, 'Изменения сохранены')
            return redirect(wallet.get_absolute_url())
    else:
        form = WalletEditForm(initial={'name': wallet.name,
                                       'balance': wallet.balance,
                                       'currency': wallet.currency,
                                       'is_archive': wallet.is_archive,
                                       })
    
    context = {'form': form,
               'title': 'Изменение счёта',
               'wallet': wallet,
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/wallet_edit.html', context)


@login_required(login_url='about')
def wallet_delete(request, pk):
    
    def confirm_delete(wal, request):
        wal_name = wal.name
        wal.delete()
        messages.success(request, f'Счёт "{wal_name}" успешно удалён!')
        return redirect('wallets')

    wallet = Wallet.objects.get(pk=pk)
    if wallet.user != request.user:
        messages.error(request, 'У вас нет прав для удаления чужого счёта!')
        return redirect('wallets')
    
    wallets_exclude_current = Wallet.objects.filter(user=request.user).exclude(pk=pk)
    operations_to_move = Operation.objects.filter(Q(user=request.user) & (Q(from_wallet=pk) | Q(to_wallet=pk)))
    operations_count = operations_to_move.count()
    
    if operations_count == 0:
        return confirm_delete(wallet, request)
    
    # Блок, который срабатывает при подтверждении удаления счёта - при выборах переноса или удаления операций.
    if request.GET.get('confirm', False):
        move_to = request.GET.get('move_to', False)
        
        if move_to:  # удалить с переносом операций на другой счёт
            # проверка чтобы не перенести операции на чужой кошелёк
            if int(move_to) in wallets_exclude_current.values_list('pk', flat=True):
                operations_to_move.filter(from_wallet=pk).update(from_wallet=int(move_to))
                operations_to_move.filter(to_wallet=pk).update(to_wallet=int(move_to))
                return confirm_delete(wallet, request)
        else:  # удалить с удалением операций
            operations_to_move.delete()
            return confirm_delete(wallet, request)
        
    context = {'title': f'Удаление счёта "{wallet.name}"',
               'wallet': wallet,
               'wallets_exclude_current': wallets_exclude_current,
               'operations_count': operations_count
               }
    context.update(universal_context(request))
    return render(request, 'sym_app/wallet_delete.html', context)


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


class CategoryDetail(LoginRequiredMixin, DetailView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    model = Category
    template_name = 'sym_app/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(universal_context(self.request))
        context['title'] = 'Детали категории'
        return context


@login_required(login_url='about')
def category_new(request):
    if request.method == 'POST':
        form = CategoryNewForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            if data['budget_amount'] is None:
                data['budget_amount'] = 0
            category = Category.objects.create(**data)
            print('Новая категория:', category)
            messages.success(request, f'Категория "{category}" добавлена')
            return redirect('categories')
    else:
        form = CategoryNewForm(initial={'type_of': 'pay'})
    
    context = {'form': form,
               'title': 'Добавление категории',
               'types': ('pay', 'earn')
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/category_new.html', context)


@login_required(login_url='about')
def category_edit(request, pk):
    category = Category.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = CategoryEditForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            Category.objects.filter(pk=pk).update(**data)
            print('Изменена категория:', category)
            messages.success(request, 'Изменения сохранены')
            return redirect(category.get_absolute_url())
    else:
        form = CategoryEditForm(initial={'type_of': category.type_of,
                                         'name': category.name,
                                         'is_budget': category.is_budget,
                                         'budget_amount': category.budget_amount,
                                         'is_archive': category.is_archive,
                                         })
    
    context = {'form': form,
               'title': 'Изменение категории',
               'category': category,
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/category_edit.html', context)


@login_required(login_url='about')
def category_delete(request, pk):
    
    def confirm_delete(cat, request):
        cat_name = cat.name
        cat.delete()
        messages.success(request, f'Категория "{cat_name}" успешно удалена!')
        return redirect('categories')
    
    category = Category.objects.get(pk=pk)
    
    if category.user != request.user:
        messages.error(request, 'У вас нет прав для удаления чужой категории!')
        return redirect('categories')
    if category.type_of == 'transfer':
        messages.error(request, 'Нельзя удалить категорию "Переводы"')
        return redirect('categories')
        
    categories_exclude_current = Category.objects.filter(user=request.user, type_of=category.type_of).exclude(pk=pk)
    operations_to_move = Operation.objects.filter(user=request.user, category=pk)
    operations_count = operations_to_move.count()
    
    if operations_count == 0:
        return confirm_delete(category, request)
    
    # Блок, который срабатывает при подтверждении удаления категории - при выборах переноса или удаления операций.
    if request.GET.get('confirm', False):
        move_to = request.GET.get('move_to', False)
        
        if move_to:  # удалить с переносом операций на другую категорию
            
            # проверка чтобы не перенести операции на чужую категорию
            if int(move_to) in categories_exclude_current.values_list('pk', flat=True):
                operations_to_move.update(category=int(move_to))
                return confirm_delete(category, request)
            else:
                messages.error(request, 'Нельзя перенести операции на данную категорию! Она чужая или не того типа!')
                return redirect('categories')
            
        else:  # удалить с удалением операций
            operations_to_move.delete()
            return confirm_delete(category, request)
    
    context = {'title': f'Удаление категории "{category.name}"',
               'category': category,
               'categories_exclude_current': categories_exclude_current,
               'operations_count': operations_count,
               }
    context.update(universal_context(request))
    return render(request, 'sym_app/category_delete.html', context)


class Settings(LoginRequiredMixin, UpdateView):
    # Для миксина LoginRequiredMixin
    
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
