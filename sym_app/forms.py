import re

from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.http import HttpRequest

from .models import *


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Подтверждения пароля', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
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
    
    def clean_currency1(self):
        data = self.cleaned_data
        if data['from_wallet'] and data['currency1'] != data['from_wallet'].currency:
            raise ValidationError(f"""Ошибка. Валюта списания со счёта "{data["from_wallet"]}" не совпадает
            c валютой самого счёта. Укажите валюту списания {data["from_wallet"].currency}.""")
        return data['currency1']
    
    # Кастомная валидация, срабатывает автоматически для поля currency1
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

    # Кастомная валидация, срабатывает автоматически для поля currency2
    def clean_amount2(self):
        data = self.cleaned_data
        if 'amount2' not in data.keys():
            data['amount2'] = data['amount1']
        return data['amount2']
    
    # Кастомная валидация, срабатывает если указана категория "Перевод"
    def clean_to_wallet(self):
        data = self.cleaned_data
        if data['category'].type_of == 'transfer':
            if ('from_wallet' not in data.keys()) or ('to_wallet' not in data.keys() or (not data['to_wallet']) or (not data['from_wallet'])):
                raise ValidationError('Ошибка. Для перевода нужно указать два счёта. Пожалуйста, укажите счета.')
            if data['from_wallet'] == data['to_wallet']:
                raise ValidationError('Ошибка. Для перевода нужно указать разные счета. Пожалуйста, выберите другой счёт.')
        else:
            data['to_wallet'] = None
        return data['to_wallet']
    
    def clean_exchange_rate(self):
        data = self.cleaned_data
        if 'amount2' in data.keys():
            data['exchange_rate'] = data['amount1'] / data['amount2']
        else:
            data['exchange_rate'] = 1
        return data['exchange_rate']


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
    
    def __init__(self, *args, **kwargs):
        super(CategoryEditForm, self).__init__(*args, **kwargs)
        self.fields['type_of'].queryset = ('Расходы', 'Доходы')
        
    class Meta:
        model = Category
        fields = ('name', 'type_of', 'is_budget', 'budget_amount', 'is_archive',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of': forms.Select(attrs={'class': 'form-select'}),
            'is_budget': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'onchange': 'active_disable_budget()'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
            'is_archive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
