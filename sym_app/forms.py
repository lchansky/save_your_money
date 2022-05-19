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


class OperationNewForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(OperationNewForm, self).__init__(*args, **kwargs)
        self.fields['from_wallet_id'].queryset = Wallet.objects.filter(user=self.request.user)
        self.fields['category_id'].queryset = Category.objects.filter(user=self.request.user)
        self.fields['to_wallet_id'].queryset = Wallet.objects.filter(user=self.request.user)
        
    class Meta:
        model = Operation
        fields = [
            'updated_at', 'from_wallet_id', 'category_id', 'to_wallet_id',
            'currency1', 'amount1', 'currency2', 'amount2', 'description'
        ]
        widgets = {
            'updated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'from_wallet_id': forms.Select(attrs={'class': 'form-select'}),
            'category_id': forms.Select(attrs={'class': 'form-select', 'onchange': 'enable_or_disable_wallet2(this.value)'}),
            'to_wallet_id': forms.Select(attrs={'class': 'form-select', 'disabled': ''}),
            'currency1': forms.Select(attrs={'class': 'form-select', 'onchange': 'same_or_not_currencies()'}),
            'amount1': forms.NumberInput(attrs={'class': 'form-control', 'onchange': 'change_amount2_by_amount1()'}),
            'currency2': forms.Select(attrs={'class': 'form-select', 'onchange': 'same_or_not_currencies()'}),
            'amount2': forms.NumberInput(attrs={'class': 'form-control', 'disabled': ''}),
            'description': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'from_wallet_id': 'Счёт',
            'to_wallet_id': 'Счёт получения'
        }
        
        help_texts = {
            'to_wallet_id':  'Чтобы перевести деньги со счёта на счёт, выберите "Переводы"'
        }
    
    # Кастомная валидация, срабатывает если указана категория "Перевод"
    def clean_to_wallet_id(self):
        data = self.cleaned_data
        if data['category_id'].type_of == 'transfer':
            if data['from_wallet_id'] == data['to_wallet_id']:
                raise ValidationError('Ошибка. Для перевода нужно указать разные счета. Пожалуйста, выберите другой счёт.')
            if not (data['from_wallet_id'] and data['to_wallet_id']):
                raise ValidationError('Ошибка. Для перевода нужно указать оба счёта. Пожалуйста, укажите счета.')
        else:
            print('Проверка НЕ сработала, категория НЕ transfer!')
            data['to_wallet_id'] = None
    
        return data['to_wallet_id']
    
    

