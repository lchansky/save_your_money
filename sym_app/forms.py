import re
from datetime import datetime

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
            'currency1', 'amount1', 'currency2', 'amount2', 'description'
        )
        widgets = {
            'updated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'from_wallet': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select', 'onchange': 'enable_or_disable_wallet2(this.value)'}),
            'to_wallet': forms.Select(attrs={'class': 'form-select', 'disabled': ''}),
            'currency1': forms.Select(attrs={'class': 'form-select', 'onchange': 'same_or_not_currencies()'}),
            'amount1': forms.NumberInput(attrs={'class': 'form-control', 'onchange': 'change_amount2_by_amount1()'}),
            'currency2': forms.Select(attrs={'class': 'form-select', 'onchange': 'same_or_not_currencies()'}),
            'amount2': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
            'description': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'from_wallet': 'Счёт',
            'to_wallet': 'Счёт получения'
        }
        
        help_texts = {
            'to_wallet':  'Чтобы перевести деньги со счёта на счёт, выберите категорию "Переводы"'
        }
    
    # Кастомная валидация, срабатывает если указана категория "Перевод"
    def clean_to_wallet(self):
        data = self.cleaned_data
        if data['category'].type_of == 'transfer':
            if data['from_wallet'] == data['to_wallet']:
                raise ValidationError('Ошибка. Для перевода нужно указать разные счета. Пожалуйста, выберите другой счёт.')
            if not (data['from_wallet'] and data['to_wallet']):
                raise ValidationError('Ошибка. Для перевода нужно указать оба счёта. Пожалуйста, укажите счета.')
        else:
            print('Проверка НЕ сработала, категория НЕ transfer!')
            data['to_wallet'] = None
    
        return data['to_wallet']


class OperationEditForm(OperationNewForm):
    pass
    
    

