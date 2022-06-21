import datetime as dt
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import pytz
import requests
from google_currency import convert, CODES
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import ListView, UpdateView, DetailView, FormView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from sym_django.settings import TIME_ZONE
from .decorators import check_permissions
from .forms import *
from sym_app.utils.utils import universal_context, load_exchange_rates_pks, load_wallets_currencies


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
        form = UserRegisterForm(data=request.POST)
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


class Operations(LoginRequiredMixin, FormView, ListView):
    redirect_field_name = None  # Для миксина LoginRequiredMixin
    login_url = 'about'  # Для миксина LoginRequiredMixin
    
    def get(self, request, *args, **kwargs):
        return render(request, 'sym_app/operations.html', context=self.get_context())
    
    def post(self, request, *args, **kwargs):
        filter_dict = dict(self.get_form_kwargs()['data'])
        filter_dict.pop('csrfmiddlewaretoken')
        filter_dict_copy = filter_dict.copy()
        for k, v in filter_dict_copy.items():
            if v == ['', ]:
                filter_dict.pop(k)
            else:
                filter_dict[k] = v[0]
        query_string = urlencode(filter_dict)
        base_url = reverse('operations')
        url = f'{base_url}?{query_string}'  # /operations/?category=42
        return redirect(url)
    
    def get_context(self):
        context = {}
        context['title'] = 'Список операций'
        context['operations_in_days'] = self.get_operations_in_days()
        context['form'] = OperationFilterForm(request=self.request, initial=self.request.GET)
        context.update(universal_context(self.request))
        return context
    
    def get_operations_in_days(self):
        """Возвращает словарь, где ключи - даты, а значения - списки из операций в эту дату {date: [operations]}"""
        operations = (Operation.objects
                      .filter(self.url_filtering())
                      .select_related('category', 'from_wallet', 'to_wallet', 'currency1', 'currency2'))
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
    
    def url_filtering(self):
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
    operation = Operation.objects.select_related(
        'from_wallet', 'to_wallet', 'category', 'currency1', 'currency2').get(pk=pk)
    operation.delete_from_view()
    messages.success(request, 'Операция успешно удалена')
    return redirect('home')


@login_required(login_url='about')
def operation_new(request):
    if request.method == 'POST':
        form = OperationNewForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.custom_cleaned_data(request)
            Operation.create_from_view(data)
            messages.success(request, 'Операция добавлена')
            return redirect('home')
    else:
        form = OperationNewForm(request=request,
                                initial={'from_wallet': Wallet.objects.filter(user=request.user).first()})

    context = {'title': 'Добавление операции',
               'form': form,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': load_wallets_currencies(request),
               'exchange_rates_pks': load_exchange_rates_pks(),
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/operation_new.html', context)


@login_required(login_url='about')
@check_permissions(model=Operation, redirect_page='operations')
def operation_duplicate(request, pk):
    operation = Operation.objects.select_related(
        'from_wallet', 'to_wallet', 'category', 'currency1', 'currency2').get(pk=pk)
    operation_fields = Operation.objects.values().get(pk=pk)
    
    if request.method == 'POST':
        form = OperationNewForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.custom_cleaned_data(request)
            created_operation = Operation.create_from_view(data)
            messages.success(request, 'Операция добавлена')
            return redirect(created_operation.get_absolute_url())
    else:
        form = OperationNewForm(request=request,
                                initial=OperationNewForm.initial_fields(operation_fields))
        
    context = {'title': 'Добавление операции',
               'form': form,
               'operation': operation,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': load_wallets_currencies(request),
               'exchange_rates_pks': load_exchange_rates_pks(),
               }
    context.update(universal_context(request))
    
    return render(request, 'sym_app/operation_duplicate.html', context)


@login_required(login_url='about')
@check_permissions(model=Operation, redirect_page='operations')
def operation_edit(request, pk):
    operation = Operation.objects.select_related('from_wallet', 'to_wallet', 'category').get(pk=pk)
    operation_fields = Operation.objects.values().get(pk=pk)
    if request.method == 'POST':
        form = OperationEditForm(data=request.POST, request=request)
        if form.is_valid():
            data = form.custom_cleaned_data(request)
            operation.edit_from_view(data)
            messages.success(request, 'Изменения сохранены')
            return redirect(operation.get_absolute_url())
    else:
        form = OperationEditForm(request=request,
                                 initial=OperationEditForm.initial_fields(operation_fields))

    context = {'title': 'Редактирование операции',
               'form': form,
               'operation': operation,
               'transfer_category': Category.objects.get(user=request.user, type_of='transfer').pk,
               'wallets_currency_dict': load_wallets_currencies(request),
               'exchange_rates_pks': load_exchange_rates_pks(),
               }
    context.update(universal_context(request))

    return render(request, 'sym_app/operation_edit.html', context)


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
            
            Wallet.objects.create(**data)
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
    
    # Блок парсинга курса Рубля ПМР
    rup = Currency.objects.get(name='RUP')
    response = requests.get("https://www.agroprombank.com/xmlinformer.php")
    root = ET.fromstring(response.text)
    rup_rate = float(root[1][2].findtext('currencySell'))
    rup.exchange_rate = 1 / rup_rate
    rup.exchange_rate_reverse = rup_rate
    rup.save()
    
    # Блок парсинга всех остальных валют
    for currency in currencies:  # берём по одной валюте из БД
        if currency.name in CODES.keys() and currency.exchange_to in CODES.keys():
            converted = json.loads(convert(currency.name, currency.exchange_to, 1000))
            # 1000 для точности, больше знаков после запятой
            currency.exchange_rate = float(converted['amount']) / 1000
            currency.exchange_rate_reverse = 1000 / float(converted['amount'])
            currency.save()
    
    # Блок записи в JSON
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


    