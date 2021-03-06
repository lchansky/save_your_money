import re
from pprint import pprint

import pytz
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.http import HttpRequest

from sym_django.settings import TIME_ZONE
from .models import *


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label='Имя пользователя',
                               widget=forms.TextInput(attrs={'class': 'form-control'}),
                               help_text='Обязательное поле. Не более 150 символов. Только буквы, цифры и символы @/./+/-/_.')
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Пароль',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                help_text="""Минимум 8 символов.
                                             Пароль не должен содержать вашу личную информацию,
                                             не должен быть слишком простым, не должен состоять только из цифр.""")
    password2 = forms.CharField(label='Подтверждения пароля',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'main_currency', 'budget')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'main_currency': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'name': 'Имя (отображается на панели навигации сверху)',
        }


class OperationNewForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(OperationNewForm, self).__init__(*args, **kwargs)
        self.fields['from_wallet'].queryset = Wallet.objects.filter(user=self.request.user)
        self.fields['category'].queryset = Category.objects.filter(user=self.request.user)
        self.fields['to_wallet'].queryset = Wallet.objects.filter(user=self.request.user)
        
    class Meta:
        model = Operation
        fields = (
            'updated_at', 'from_wallet', 'category', 'to_wallet',
            'currency1', 'amount1', 'exchange_rate', 'currency2', 'amount2', 'description'
        )
        widgets = {
            'updated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'from_wallet': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'transfer_check(this), change_currency1(this.value), rates(), same_or_not_currencies()'}),
            'category': forms.Select(attrs={'class': 'form-select fs-6', 'onchange': 'if_transfer()'}),
            'to_wallet': forms.Select(attrs={
                'class': 'form-select',
                'disabled': '',
                'onchange': 'transfer_check(this), change_currency2(this.value), rates(), same_or_not_currencies()'}),
            'currency1': forms.Select(attrs={'class': 'form-select', 'onchange': 'rates(), same_or_not_currencies()', 'disable': ''}),
            'amount1': forms.NumberInput(attrs={'class': 'form-control', 'onchange': 'change_amount2_by_amount1()'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
            'currency2': forms.Select(attrs={'class': 'form-select', 'onchange': 'rates(), same_or_not_currencies()'}),
            'amount2': forms.NumberInput(attrs={'class': 'form-control', 'disabled': '', 'onchange': 'change_amount1_by_amount2()'}),
            'description': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'from_wallet': 'Счёт',
            'to_wallet': 'Счёт (перевод)',
            'amount1': 'Сумма'
        }
        
        help_texts = {
            'category':  'Для перевода между счетами выберите категорию "Переводы"'
        }

    def custom_cleaned_data(self, request):
        data = self.cleaned_data
        data['user_id'] = request.user.id
        data['amount1'] = self.clean_amount1()
        data['amount2'] = self.clean_amount2()
        data['exchange_rate'] = self.clean_exchange_rate()
        data['to_wallet'] = self.clean_to_wallet()
        data['currency1'] = self.clean_currency1()
        data['currency2'] = self.clean_currency2()
        return data

    # Кастомная валидация, срабатывает автоматически для поля currency1
    def clean_currency1(self):
        data = self.cleaned_data
        if data.get('from_wallet', False) and data['currency1'] != data['from_wallet'].currency:
            raise ValidationError(f"""Ошибка. Валюта списания со счёта "{data["from_wallet"]}" не совпадает
            c валютой самого счёта. Укажите валюту списания {data["from_wallet"].currency}.""")
        return data['currency1']

    # Кастомная валидация, срабатывает автоматически для поля amount1
    def clean_amount1(self):
        data = self.cleaned_data
        if data.get('amount1', 0) == 0:
            raise ValidationError(
                f'Ошибка. Суммы не должны равняться нулю. Пожалуйста, введите корректные значения')
        if data['category'].type_of == 'transfer' and data.get('amount1', 0) <= 0:
            raise ValidationError(
                f'Ошибка. При переводе суммы должны быть больше нуля. Пожалуйста, введите корректные значения')
        return data['amount1']

    # Кастомная валидация, срабатывает автоматически для поля amount2
    def clean_amount2(self):
        data = self.cleaned_data
        if 'amount2' not in data.keys():
            data['amount2'] = self.clean_amount1()
        if data.get('amount1', 0) == 0:
            raise ValidationError(
                f'Ошибка. Суммы не должны равняться нулю. Пожалуйста, введите корректные значения')
        if data['category'].type_of == 'transfer' and data.get('amount2', 0) <= 0:
            raise ValidationError(
                f'Ошибка. При переводе суммы должны быть больше нуля. Пожалуйста, введите корректные значения')
        return data['amount2']

    def clean_exchange_rate(self):
        data = self.cleaned_data
        data['exchange_rate'] = self.clean_amount1() / self.clean_amount2()
        return data['exchange_rate']
    
    # Кастомная валидация, срабатывает автоматически для поля currency2
    def clean_currency2(self):
        data = self.cleaned_data
        # if not data['currency2']:
        #     if data['category'].type_of == 'transfer' and data['to_wallet']:
        #         data['currency2'] = data['to_wallet'].currency
        #     else:
        #         data['currency2'] = data['from_wallet'].currency
        
        if 'to_wallet' in data.keys() and data['to_wallet'] and data['currency2'] != data['to_wallet'].currency:
            raise ValidationError(f"""Ошибка. Валюта получения перевода на счёт "{data["to_wallet"]}" не совпадает
            c валютой самого счёта. Укажите "Валюту платежа" {data["to_wallet"].currency}.""")
        return data['currency2']
    
    def clean_to_wallet(self):
        data = self.cleaned_data
        if data['category'].type_of == 'transfer':
            if ('from_wallet' not in data.keys() or 'to_wallet' not in data.keys()
                    or not data['to_wallet'] or not data['from_wallet']):
                raise ValidationError('Ошибка. Для перевода нужно указать два счёта. Пожалуйста, укажите счета.')
            if data['from_wallet'] == data['to_wallet']:
                raise ValidationError(
                    'Ошибка. Для перевода нужно указать разные счета. Пожалуйста, выберите другой счёт.')
        else:
            data['to_wallet'] = None
        return data['to_wallet']
    
    @staticmethod
    def initial_fields(fields: dict):
        # Добавляю дельту таймзоны, т.к. в БД время в UTC.
        dt_with_tz = fields['updated_at'].astimezone(tz=pytz.timezone(TIME_ZONE))
        
        # HTML понимает только формат 'yyyy-mm-ddThh:mm'
        initial = {'updated_at': dt_with_tz.strftime('%Y-%m-%dT%H:%M'),
                   'from_wallet': fields['from_wallet_id'],
                   'category': fields['category_id'],
                   'to_wallet': fields['to_wallet_id'],
                   'currency1': fields['currency1_id'],
                   'amount1': fields['amount1'],
                   'currency2': fields['currency2_id'],
                   'amount2': fields['amount2'],
                   'description': fields['description'],
                   }
        return initial
    

class OperationEditForm(OperationNewForm):
    pass


class WalletNewForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ('name', 'balance', 'currency',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'name': 'Например: "Долларовый счёт в банке", "Карта VISA" или "Заначка"',
            'balance': 'Введите актуальный баланс вашего счёта'
        }


class WalletEditForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ('name', 'balance', 'currency', 'is_archive')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'is_archive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'currency':  'Смена валюты счёта не затронет старые операции'
        }


class CategoryNewForm(forms.ModelForm):
        
    class Meta:
        model = Category
        fields = ('name', 'type_of', 'is_budget', 'budget_amount',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of': forms.TextInput(attrs={'class': 'form-control', 'hidden': ''}),
            'is_budget': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'onchange': 'active_disable_budget()'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
        }
        help_texts = {'type_of': ''}
        labels = {'type_of': ''}


class CategoryEditForm(forms.ModelForm):
    
    # def __init__(self, *args, **kwargs):
    #     super(CategoryEditForm, self).__init__(*args, **kwargs)
    #     self.fields['type_of'].queryset = ('Расходы', 'Доходы')
        
    class Meta:
        model = Category
        fields = ('name', 'type_of', 'is_budget', 'budget_amount', 'is_archive',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of': forms.TextInput(attrs={'class': 'form-control', 'hidden': ''}),
            'is_budget': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'onchange': 'active_disable_budget()'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
            'is_archive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {'type_of': ''}
        labels = {'type_of': ''}


class OperationFilterForm(forms.Form):
        
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='От',
        required=False,
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='До',
        required=False,
    )
    type_of = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=(('', ''), ('pay', 'Расходы'), ('earn', 'Доходы'), ('transfer', 'Переводы')),
        required=False,
        label='Тип',
    )
    category = forms.ModelChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        queryset=None,
        label='Категория',
    )

    wallet = forms.ModelChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        queryset=None,
        label='Счёт',
    )

    description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label='Описание',
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(OperationFilterForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=self.request.user)
        self.fields['wallet'].queryset = Wallet.objects.filter(user=self.request.user)
    