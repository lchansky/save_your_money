from django.db import models

"""
    ЗДЕСЬ В АТРИБУТАХ МОДЕЛЕЙ, ГДЕ ЕСТЬ ForeignKey МОЖНО ПОПРОБОВАТЬ ЮЗАТЬ
    related_name='name' ЧТОБЫ В ТАБЛИЦЕ-ПРЕДКЕ ПОЯВИЛОСЬ ПОЛЕ, В КОТОРОМ
    БУДЕТ УКАЗЫВАТЬСЯ, КАКИЕ ЗАПИСИ В ТАБЛИЦЕ-ПОТОМКЕ ПРИНАДЛЕЖАТ К ЭТОМУ ПОЛЮ
"""


# class Wallet(models.Model):
#     user_id = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='ID пользователя')
#     name = models.CharField(max_length=150, verbose_name='Название счёта')
#     balance = models.FloatField(default=0)
#     currency = models.ForeignKey('Currency', verbose_name='ID валюты', on_delete=models.PROTECT)
#     is_archive = models.BooleanField(verbose_name='Архивный счёт?')
#
#
# class Category(models.Model):
#     user_id = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='ID пользователя')
#     name = models.CharField(max_length=150, verbose_name='Название категории')
#     type_of = models.CharField(max_length=10, verbose_name='Тип категории')
#     is_budget = models.BooleanField(verbose_name='Бюджет вкл./выкл.', default=False)
#     budget_amount = models.FloatField(verbose_name='Размер бюджета')
#     is_archive = models.BooleanField(verbose_name='Архивная категория?', default=False)
#
#
# class Operation(models.Model):
#     user_id = models.ForeignKey(
#         'User', verbose_name='ID пользователя', on_delete=models.CASCADE)
#
#     updated_at = models.DateTimeField(
#         verbose_name='Дата и время операции')
#
#     from_wallet_id = models.ForeignKey(
#         'Wallet',
#         verbose_name='ID счёта списания',
#         on_delete=models.CASCADE)
#
#     to_category_id = models.ForeignKey(
#         'Category',
#         verbose_name='ID категории',
#         on_delete=models.CASCADE)
#
#     to_wallet_id = models.ForeignKey(
#         'Wallet',
#         verbose_name='ID счёта получения',
#         on_delete=models.CASCADE,
#         blank=True,
#         default=None)
#
#     currency1 = models.ForeignKey(
#         'Currency', verbose_name='ID валюты списания', on_delete=models.PROTECT)
#
#     currency2 = models.ForeignKey(
#         'Currency', verbose_name='ID валюты списания', on_delete=models.PROTECT, default=currency1)
#
#     description = models.CharField(
#         max_length=150, verbose_name='Описание операции')
#
#
# class User(models.Model):
#     pass


class Currency(models.Model):
    name = models.CharField(max_length=20, verbose_name='Валюта')
    exchange_to = models.CharField(max_length=20, verbose_name='Валюта для обмена')
    exchange_rate = models.FloatField(verbose_name='Курс валюты')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'
        ordering = ['id']


# class UserSettings(models.Model):
#     # user_id = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='ID пользователя')
#     main_currency = models.ForeignKey('Currency', default=1, on_delete=models.PROTECT)
#     budget = models.BooleanField(blank=True, default=False)
    
    
