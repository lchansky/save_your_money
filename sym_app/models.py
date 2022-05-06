from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from sym_app.utils import default_user_settings

"""
    ЗДЕСЬ В АТРИБУТАХ МОДЕЛЕЙ, ГДЕ ЕСТЬ ForeignKey МОЖНО ПОПРОБОВАТЬ ЮЗАТЬ
    related_name='name' ЧТОБЫ В ТАБЛИЦЕ-ПРЕДКЕ ПОЯВИЛОСЬ ПОЛЕ, В КОТОРОМ
    БУДЕТ УКАЗЫВАТЬСЯ, КАКИЕ ЗАПИСИ В ТАБЛИЦЕ-ПОТОМКЕ ПРИНАДЛЕЖАТ К ЭТОМУ ПОЛЮ
"""


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


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=150, verbose_name='Название счёта')
    balance = models.FloatField(default=0)
    currency = models.ForeignKey('Currency', verbose_name='ID валюты', on_delete=models.PROTECT)
    is_archive = models.BooleanField(verbose_name='Архивный счёт?', blank=True, default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ['user', 'pk']


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', blank=True)
    name = models.CharField(max_length=150, verbose_name='Название категории')
    type_of = models.CharField(max_length=10, verbose_name='Тип категории')
    is_budget = models.BooleanField(verbose_name='Бюджет вкл./выкл.', blank=True, default=False)
    budget_amount = models.FloatField(verbose_name='Размер бюджета', blank=True, default=0)
    is_archive = models.BooleanField(verbose_name='Архивная категория?', blank=True, default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['user', 'pk']


class Operation(models.Model):
    user = models.OneToOneField(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    
    updated_at = models.DateTimeField(verbose_name='Дата и время операции')
    
    from_wallet_id = models.ForeignKey('Wallet',
                                       verbose_name='ID счёта списания',
                                       on_delete=models.CASCADE,
                                       related_name='from_wallet')
    
    category_id = models.ForeignKey('Category',
                                    verbose_name='ID категории',
                                    on_delete=models.CASCADE)
    
    to_wallet_id = models.ForeignKey('Wallet',
                                     verbose_name='ID счёта получения',
                                     on_delete=models.CASCADE,
                                     blank=True,
                                     default=None,
                                     related_name='to_wallet',
                                     null=True)
    
    currency1 = models.ForeignKey('Currency',
                                  verbose_name='ID валюты списания',
                                  on_delete=models.PROTECT,
                                  related_name='currency1')
    
    amount1 = models.FloatField(verbose_name='Сумма списания')
    
    currency2 = models.ForeignKey('Currency',
                                  verbose_name='ID валюты платежа',
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  default=None,
                                  related_name='currency2')
    
    amount2 = models.FloatField(verbose_name='Сумма платежа')

    description = models.CharField(max_length=150, verbose_name='Описание операции', blank=True)
    
    def __str__(self):
        return f'Операция {self.pk} пользователя {self.user}'

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['pk']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=30, verbose_name='Имя', blank=True)
    main_currency = models.ForeignKey('Currency', default=1, on_delete=models.PROTECT)
    budget = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.objects.get(pk=self.kwargs['user'])

    class Meta:
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователей'
        ordering = ['user']


class DefaultCategories(models.Model):
    category_type_of = models.CharField(max_length=10, verbose_name='Тип')
    category_name = models.CharField(max_length=150, verbose_name='Название')
    
    class Meta:
        verbose_name = 'Дефолтные категории'
        verbose_name_plural = 'Дефолтные категории'
        ordering = ['category_type_of', 'pk']
    
    
class DefaultWallets(models.Model):
    wallet_name = models.CharField(max_length=150, verbose_name='Название')

    class Meta:
        verbose_name = 'Дефолтные счета'
        verbose_name_plural = 'Дефолтные счета'
        ordering = ['wallet_name', 'pk']
    

# Декоратор ресивер отлавливает изменения в модели User, встроенной в Джанго
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Если пользователь зарегистрировался - функция запускает создание для него
    дефолтных параметров, категорий, счетов. Если произошли изменения в модели User
    - то подтягивает изменения во все связанные кастомные модели"""
    if created:
        default_user_settings(instance)
    instance.profile.save()
