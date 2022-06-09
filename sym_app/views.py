import datetime as dt
from pprint import pprint
import pytz
from pytz import UTC
from google_currency import convert, CODES
import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import ListView, UpdateView, DetailView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F

from sym_django.settings import TIME_ZONE
from .decorators import check_permissions
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
        context.update(universal_context(self.request))
        return context
    
    def get_operations_in_days(self):
        """Возвращает словарь, где ключи - даты, а значения - списки из операций в эту дату {date: [operations]}"""
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
        """Собирает параметры запроса к БД, где user это текущий пользователь,
        а все остальные параметры берутся из URL адреса"""
        kwargs = {}
        kwargs['user'] = self.request.user
        q = Q(user=kwargs['user'])
        
        kwargs['category__type_of'] = self.request.GET.get('type_of', False)
        if kwargs['category__type_of']:
            q = q & Q(category__type_of=kwargs['category__type_of'])
        
        kwargs['category'] = self.request.GET.get('category', False)
        if kwargs['category']:
            q = q & Q(category=kwargs['category'])
        
        kwargs['description'] = self.request.GET.get('description', False)
        if kwargs['description']:
            q = q & Q(description__icontains=kwargs['description'])
            # Чувствителен к регистру из-за SQlite. В других бд норм
        
        kwargs['date_from'] = self.request.GET.get('date_from', False)
        if kwargs['date_from']:
            kwargs['date_from'] = dt.datetime.strptime(kwargs['date_from'], '%Y-%m-%d')
        kwargs['date_to'] = self.request.GET.get('date_to', False)
        if kwargs['date_to']:
            kwargs['date_to'] = dt.datetime.strptime(kwargs['date_to'], '%Y-%m-%d')
        if kwargs['date_from'] and kwargs['date_to']:
            if kwargs['date_from'] > kwargs['date_to']:
                kwargs['date_from'], kwargs['date_to'] = kwargs['date_to'], kwargs['date_from']
            if kwargs['date_to'] < dt.datetime.max - dt.timedelta(1):
                kwargs['date_to'] += dt.timedelta(1)
            q = q & Q(updated_at__gte=kwargs['date_from']) & Q(updated_at__lte=kwargs['date_to'])
        else:
            if kwargs['date_from']:
                q = q & Q(updated_at__gte=kwargs['date_from'])
            if kwargs['date_to']:
                if kwargs['date_to'] < dt.datetime.max - dt.timedelta(1):
                    kwargs['date_to'] += dt.timedelta(1)
                q = q & Q(updated_at__lte=kwargs['date_to'])
        
        wallet = self.request.GET.get('wallet', False)
        if wallet:
            kwargs['from_wallet__pk'] = wallet
            kwargs['to_wallet__pk'] = wallet
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
@check_permissions(model=Operation, redirect_page='operations')
def operation_delete(request, pk):
    operation = Operation.objects.get(pk=pk)

    # Сбор параметров операции для изменения балансов (ниже)
    from_wallet_old = operation.from_wallet
    to_wallet_old = operation.to_wallet
    type_of_old = operation.category.type_of
    amount1_old = operation.amount1
    amount2_old = operation.amount2
    
    # Удаление операции
    operation.delete()

    # Откат балансов
    if type_of_old == 'pay':
        from_wallet_old.inc_balance(amount1_old)
    elif type_of_old == 'earn':
        from_wallet_old.dec_balance(amount1_old)
    elif type_of_old == 'transfer':
        from_wallet_old.inc_balance(amount1_old)
        to_wallet_old.dec_balance(amount2_old)
        
    messages.success(request, 'Операция успешно удалена')
    return redirect('home')


@login_required(login_url='about')
@check_permissions(model=Operation, redirect_page='operations')
def operation_duplicate(request, pk):
    operation = Operation.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = OperationNewForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            data['amount1'] = form.clean_amount1()
            data['amount2'] = form.clean_amount2()
            data['exchange_rate'] = form.clean_exchange_rate()
            data['to_wallet'] = form.clean_to_wallet()
            data['currency1'] = form.clean_currency1()
            data['currency2'] = form.clean_currency2()

            # Создание записи в БД
            created_operation = Operation.objects.create(**data)

            # Изменение балансов кошельков
            if data['category'].type_of == 'pay':
                data['from_wallet'].dec_balance(data['amount1'])
            elif data['category'].type_of == 'earn':
                data['from_wallet'].inc_balance(data['amount1'])
            elif data['category'].type_of == 'transfer':
                data['from_wallet'].dec_balance(data['amount1'])
                data['to_wallet'].inc_balance(data['amount2'])
            
            messages.success(request, 'Операция добавлена')
            return redirect(created_operation.get_absolute_url())
    else:
        # Добавляю дельту таймзоны, т.к. в БД время в UTC.
        dt_with_tz = operation.updated_at.astimezone(tz=pytz.timezone(TIME_ZONE))
        
        form = OperationNewForm(request=request, initial={
            'updated_at': dt_with_tz.strftime('%Y-%m-%dT%H:%M'),  # HTML понимает только формат 'yyyy-mm-ddThh:mm'
            'from_wallet': operation.from_wallet,
            'category': operation.category,
            'to_wallet': operation.to_wallet,
            'currency1': operation.currency1,
            'amount1': operation.amount1,
            'currency2': operation.currency2,
            'amount2': operation.amount2,
            'description': operation.description,
        })
    
    wallets_currency_dict = {wallet.pk: wallet.currency.pk
                             for wallet in Wallet.objects.filter(user=request.user)}
    with open('exchange_rates_pks.json', 'r') as file:
        exchange_rates_pks = file.read()
    context = {'form': form,
               'title': 'Добавление операции',
               'operation': operation,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': wallets_currency_dict,
               'exchange_rates_pks': exchange_rates_pks,
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/operation_duplicate.html', context)


@login_required(login_url='about')
@check_permissions(model=Operation, redirect_page='operations')
def operation_edit(request, pk):
    operation = Operation.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = OperationEditForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            data['user_id'] = request.user.id
            data['amount1'] = form.clean_amount1()
            data['amount2'] = form.clean_amount2()
            data['exchange_rate'] = form.clean_exchange_rate()
            data['to_wallet'] = form.clean_to_wallet()
            data['currency1'] = form.clean_currency1()
            data['currency2'] = form.clean_currency2()
            
            # Сбор параметров операции для изменения балансов (ниже)
            from_wallet_old = operation.from_wallet
            to_wallet_old = operation.to_wallet
            type_of_old = operation.category.type_of
            amount1_old = operation.amount1
            amount2_old = operation.amount2
            
            # Сохранение в БД изменённой операции
            Operation.objects.filter(pk=pk).update(**data)
            print('Изменена операция:', operation)

            # Откат балансов (как будто удаление операции)
            if type_of_old == 'pay':
                from_wallet_old.inc_balance(amount1_old)
            elif type_of_old == 'earn':
                from_wallet_old.dec_balance(amount1_old)
            elif type_of_old == 'transfer':
                from_wallet_old.inc_balance(amount1_old)
                to_wallet_old.dec_balance(amount2_old)
            
            # Изменение балансов с параметрами новой (т.е. измененной операции).
            # То есть как будто удалили старую операцию и добавили новую
            if data['category'].type_of == 'pay':
                data['from_wallet'].dec_balance(data['amount1'])
            elif data['category'].type_of == 'earn':
                data['from_wallet'].inc_balance(data['amount1'])
            elif data['category'].type_of == 'transfer':
                data['from_wallet'].dec_balance(data['amount1'])
                data['to_wallet'].inc_balance(data['amount2'])
            
            messages.success(request, 'Изменения сохранены')
            return redirect(operation.get_absolute_url())
    else:
        # Добавляю дельту таймзоны, т.к. в БД время в UTC.
        dt_with_tz = operation.updated_at.astimezone(tz=pytz.timezone(TIME_ZONE))
        
        form = OperationEditForm(request=request, initial={
            'updated_at': dt_with_tz.strftime('%Y-%m-%dT%H:%M'),  # HTML понимает только формат 'yyyy-mm-ddThh:mm'
            'from_wallet': operation.from_wallet,
            'category': operation.category,
            'to_wallet': operation.to_wallet,
            'currency1': operation.currency1,
            'amount1': operation.amount1,
            'currency2': operation.currency2,
            'amount2': operation.amount2,
            'description': operation.description,
        })

    wallets_currency_dict = {wallet.pk: wallet.currency.pk
                             for wallet in Wallet.objects.filter(user=request.user)}
    with open('exchange_rates_pks.json', 'r') as file:
        exchange_rates_pks = file.read()
    context = {'form': form,
               'title': 'Редактирование операции',
               'operation': operation,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': wallets_currency_dict,
               'exchange_rates_pks': exchange_rates_pks,
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
            data['amount1'] = form.clean_amount1()
            data['amount2'] = form.clean_amount2()
            data['exchange_rate'] = form.clean_exchange_rate()
            data['to_wallet'] = form.clean_to_wallet()
            data['currency1'] = form.clean_currency1()
            data['currency2'] = form.clean_currency2()
            
            # Создание записи в БД
            created_operation = Operation.objects.create(**data)
            
            # Изменение балансов кошельков
            if data['category'].type_of == 'pay':
                data['from_wallet'].dec_balance(data['amount1'])
            elif data['category'].type_of == 'earn':
                data['from_wallet'].inc_balance(data['amount1'])
            elif data['category'].type_of == 'transfer':
                data['from_wallet'].dec_balance(data['amount1'])
                data['to_wallet'].inc_balance(data['amount2'])
            
            print('Новая операция:', created_operation)
            messages.success(request, 'Операция добавлена')
            return redirect('home')
    else:
        form = OperationNewForm(request=request,
                                initial={'from_wallet': Wallet.objects.filter(user=request.user).first()})

    wallets_currency_dict = {wallet.pk: wallet.currency.pk
                             for wallet in Wallet.objects.filter(user=request.user)}
    with open('exchange_rates_pks.json', 'r') as file:
        exchange_rates_pks = file.read()
    
    context = {'form': form,
               'title': 'Добавление операции',
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': wallets_currency_dict,
               'exchange_rates_pks': exchange_rates_pks,
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/operation_new.html', context)


def universal_context(request):
    """Принимает запрос и контекст, добавляет к контексту те переменные, которые используются на каждой странице.
    Например, на navbar используется"""
    extra_context = {
        'optional_name': Profile.objects.get(user=request.user).name,
        'wallets': Wallet.objects.filter(user=request.user),
    }
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
@check_permissions(model=Wallet, redirect_page='wallets')
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
@check_permissions(model=Wallet, redirect_page='wallets')
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
        context['categories_pay'], context['categories_earn'] = self.categories_pay_earn()
        context['type'] = self.request.GET.get('type', False)
        context['title'] = 'Список категорий'
        if context['type'] == 'pay':
            context['title'] += ' - расходы'
            context.pop('categories_earn')
        if context['type'] == 'earn':
            context['title'] += ' - доходы'
            context.pop('categories_pay')
        context.update(universal_context(self.request))
        return context
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def categories_pay_earn(self):
        """Возвращает 2 списка - список расходных и список доходных категорий пользователя"""
        categories = self.get_queryset()
        categories_pay = categories.filter(type_of='pay')
        categories_earn = categories.filter(type_of='earn')
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
               'types': ('pay', 'earn'),
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/category_new.html', context)


@login_required(login_url='about')
@check_permissions(model=Category, redirect_page='categories')
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
               'types': ('pay', 'earn'),
               'checkbox_pay': category.type_of == 'pay',
               'checkbox_earn': category.type_of == 'earn',
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/category_edit.html', context)


@login_required(login_url='about')
@check_permissions(model=Category, redirect_page='categories')
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


def update_currencies(request):
    currencies = Currency.objects.all()
    for currency in currencies:  # берём по одной валюте из БД
        if currency.name in CODES.keys() and currency.exchange_to in CODES.keys():
            converted = json.loads(convert(currency.name, currency.exchange_to, 1000))
            # 1000 для точности, больше знаков после запятой
            currency.exchange_rate = float(converted['amount']) / 1000
            currency.exchange_rate_reverse = 1000 / float(converted['amount'])
            currency.save()
    exchange = {}
    exchange_pks = {}
    for c_outer in currencies:
        exchange[c_outer.name] = {}
        exchange_pks[c_outer.pk] = {}
        if c_outer.name in CODES.keys():
            for c_inner in currencies.exclude(pk=c_outer.pk):
                if c_inner.name in CODES.keys():
                    converted = json.loads(convert(c_inner.name, c_outer.name, 1000))
                    exchange[c_outer.name][c_inner.name] = float(converted['amount']) / 1000
                    exchange_pks[c_outer.pk][c_inner.pk] = float(converted['amount']) / 1000
                elif c_inner.exchange_to in CODES.keys():
                    converted = json.loads(convert(c_inner.exchange_to, c_outer.name, 1000))
                    exchange[c_outer.name][c_inner.name] = float(converted['amount']) / 1000 * c_inner.exchange_rate
                    exchange_pks[c_outer.pk][c_inner.pk] = float(converted['amount']) / 1000 * c_inner.exchange_rate
        elif c_outer.exchange_to in CODES.keys():
            for c_inner in currencies.exclude(pk=c_outer.pk):
                if c_inner.name in CODES.keys():
                    converted = json.loads(convert(c_inner.name, c_outer.exchange_to, 1000))
                    exchange[c_outer.name][c_inner.name] = float(converted['amount']) / 1000 / c_outer.exchange_rate
                    exchange_pks[c_outer.pk][c_inner.pk] = float(converted['amount']) / 1000 / c_outer.exchange_rate
    with open('exchange_rates.json', 'w') as file:
        json.dump(exchange, file)
    with open('exchange_rates_pks.json', 'w') as file:
        json.dump(exchange_pks, file)
    
    print('====== Обновление курсов валют прошло успешно, БД и JSON обновлены ======')
    
    return render(request, 'sym_app/about.html')
