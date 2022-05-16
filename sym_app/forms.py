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


class OperationNewForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(OperationNewForm, self).__init__(*args, **kwargs)
        self.fields['from_wallet_id'].queryset = Wallet.objects.filter(user=self.request.user)
        self.fields['category_id'].queryset = Category.objects.filter(user=self.request.user)
        self.fields['to_wallet_id'].queryset = Wallet.objects.filter(user=self.request.user)

    class Meta:
        model = Operation
        fields = ['updated_at', 'from_wallet_id', 'category_id', 'to_wallet_id',
                  'currency1', 'amount1', 'currency2', 'amount2', 'description']
        widgets = {
            'updated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'from_wallet_id': forms.Select(attrs={'class': 'form-select'}),
            'category_id': forms.Select(attrs={'class': 'form-select'}),
            'to_wallet_id': forms.Select(attrs={'class': 'form-select', 'disabled': 'true'}),
            'currency1': forms.Select(attrs={'class': 'form-select'}),
            'amount1': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency2': forms.Select(attrs={'class': 'form-select', 'disabled': 'true'}),
            'amount2': forms.NumberInput(attrs={'class': 'form-control', 'disabled': 'true'}),
            'description': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {'from_wallet_id': 'Счёт'}
        


