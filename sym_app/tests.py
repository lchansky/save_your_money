import datetime

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from .models import *


# Create your tests here.

class ViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser1111', email='test@mail.ru', password='qwerQWE1')  # также тут добавляются 11 дефолтных категорий и 2 дефолтных кошелька
        self.client.login(username='testuser1111', password='qwerQWE1')
        self.currency = Currency.objects.create(name='RUB', exchange_to='RUB', exchange_rate=1, exchange_rate_reverse=1)
    
    def test_operation_new_earn(self):
        fields = {'amount1': '200',
                  'amount2': '200',
                  'category': '1',
                  'currency1': '1',
                  'currency2': '1',
                  'description': 'Вычли из ЗП',
                  'exchange_rate': '1',
                  'from_wallet': 1,
                  'updated_at': datetime.datetime.now()}
        
        response = self.client.post(reverse('operation_new'), fields)
        
        operation = Operation.objects.get(pk=1)
        self.assertEqual(operation.amount1, float(fields['amount1']))
        self.assertEqual(operation.amount2, float(fields['amount2']))
        self.assertEqual(operation.category, Category.objects.get(pk=1))
        self.assertEqual(operation.currency1, Currency.objects.get(pk=1))
        self.assertEqual(operation.currency2, Currency.objects.get(pk=1))
        self.assertEqual(operation.description, 'Вычли из ЗП')
        self.assertEqual(operation.from_wallet.balance, 200)
        self.assertRedirects(response, reverse('home'))

    def test_operation_new_pay(self):
        fields = {'amount1': '200',
                  'amount2': '200',
                  'category': '3',
                  'currency1': '1',
                  'currency2': '1',
                  'description': 'Вычли из ЗП',
                  'exchange_rate': '1',
                  'from_wallet': 1,
                  'updated_at': datetime.datetime.now()}

        response = self.client.post(reverse('operation_new'), fields)
        operation = Operation.objects.get(pk=1)
        self.assertEqual(operation.amount1, float(fields['amount1']))
        self.assertEqual(operation.amount2, float(fields['amount2']))
        self.assertEqual(operation.category, Category.objects.get(pk=3))
        self.assertEqual(operation.currency1, Currency.objects.get(pk=1))
        self.assertEqual(operation.currency2, Currency.objects.get(pk=1))
        self.assertEqual(operation.description, 'Вычли из ЗП')
        self.assertEqual(operation.from_wallet.balance, -200)
        self.assertRedirects(response, reverse('home'))

    def test_operation_new_transfer(self):
        fields = {'amount1': '200',
                  'amount2': '200',
                  'category': '11',
                  'currency1': '1',
                  'currency2': '1',
                  'description': 'Вывел с карты в наличку',
                  'exchange_rate': '1',
                  'from_wallet': 1,
                  'to_wallet': 2,
                  'updated_at': datetime.datetime.now()}
        response = self.client.post(reverse('operation_new'), fields)
        operation = Operation.objects.get(pk=1)
        self.assertEqual(operation.amount1, float(fields['amount1']))
        self.assertEqual(operation.amount2, float(fields['amount2']))
        self.assertEqual(operation.category, Category.objects.get(pk=11))
        self.assertEqual(operation.currency1, Currency.objects.get(pk=1))
        self.assertEqual(operation.currency2, Currency.objects.get(pk=1))
        self.assertEqual(operation.description, 'Вывел с карты в наличку')
        self.assertEqual(operation.from_wallet.balance, -200)
        self.assertEqual(operation.to_wallet.balance, 200)
        self.assertRedirects(response, reverse('home'))
    
    def test_operation_new_earn_invalid(self):
        fields = {'amount1': 200,
                  'amount2': 200,
                  'category': 1,
                  'currency1': 2,
                  'currency2': 2,
                  'description': 'Зпшка пришла',
                  'exchange_rate': 1,
                  'from_wallet': 1,
                  'updated_at': datetime.datetime.now()}
        
        response = self.client.post(reverse('operation_new'), fields)
        
        operation = Operation.objects.all().first()
        self.assertEqual(operation, None)
        self.assertRedirects(response, reverse('operation_new'))

    def test_operation_new_pay_invalid(self):
        fields = {'amount1': '200',
                  'amount2': '200',
                  'category': '3',
                  'currency1': '1',
                  'currency2': '1',
                  'description': 'Вычли из ЗП',
                  'exchange_rate': '1',
                  'from_wallet': 1,
                  'updated_at': datetime.datetime.now()}

        response = self.client.post(reverse('operation_new'), fields)
        operation = Operation.objects.get(pk=1)
        self.assertEqual(operation.amount1, float(fields['amount1']))
        self.assertEqual(operation.amount2, float(fields['amount2']))
        self.assertEqual(operation.category, Category.objects.get(pk=3))
        self.assertEqual(operation.currency1, Currency.objects.get(pk=1))
        self.assertEqual(operation.currency2, Currency.objects.get(pk=1))
        self.assertEqual(operation.description, 'Вычли из ЗП')
        self.assertEqual(operation.from_wallet.balance, -200)
        self.assertRedirects(response, reverse('home'))

    def test_operation_new_transfer_invalid(self):
        fields = {'amount1': '200',
                  'amount2': '200',
                  'category': '11',
                  'currency1': '1',
                  'currency2': '1',
                  'description': 'Вывел с карты в наличку',
                  'exchange_rate': '1',
                  'from_wallet': 1,
                  'to_wallet': 2,
                  'updated_at': datetime.datetime.now()}
        response = self.client.post(reverse('operation_new'), fields)
        operation = Operation.objects.get(pk=1)
        self.assertEqual(operation.amount1, float(fields['amount1']))
        self.assertEqual(operation.amount2, float(fields['amount2']))
        self.assertEqual(operation.category, Category.objects.get(pk=11))
        self.assertEqual(operation.currency1, Currency.objects.get(pk=1))
        self.assertEqual(operation.currency2, Currency.objects.get(pk=1))
        self.assertEqual(operation.description, 'Вывел с карты в наличку')
        self.assertEqual(operation.from_wallet.balance, -200)
        self.assertEqual(operation.to_wallet.balance, 200)
        self.assertRedirects(response, reverse('home'))


#  1 тест - ✔✔✔проверить создание операции и изм. баланса кошельков при валидных данных и проверить редирект ✔
#  2 тест - проверить не создание операции с невалидными данными и чтобы баланс не изменился
#  3 тест - чтобы при запросе ГЕТ чтобы отрендерился нужный темплейт с нужным контекстом
