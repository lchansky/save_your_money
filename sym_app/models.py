from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

"""
    ЗДЕСЬ В АТРИБУТАХ МОДЕЛЕЙ, ГДЕ ЕСТЬ ForeignKey МОЖНО ПОПРОБОВАТЬ ЮЗАТЬ
    related_name='name' ЧТОБЫ В ТАБЛИЦЕ-ПРЕДКЕ ПОЯВИЛОСЬ ПОЛЕ, В КОТОРОМ
    БУДЕТ УКАЗЫВАТЬСЯ, КАКИЕ ЗАПИСИ В ТАБЛИЦЕ-ПОТОМКЕ ПРИНАДЛЕЖАТ К ЭТОМУ ПОЛЮ
"""


class Currency(models.Model):
    name = models.CharField(max_length=20, verbose_name='Валюта')
    exchange_to = models.CharField(max_length=20, verbose_name='Валюта для обмена')
    exchange_rate = models.FloatField(verbose_name='Курс (сколько стоит валюта name в валюте exchange_to)')
    exchange_rate_reverse = models.FloatField(verbose_name='Курс (сколько стоит валюта exchange_to в валюте name)')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'
        ordering = ['pk']


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=150, verbose_name='Название счёта')
    balance = models.FloatField(default=0, verbose_name='Баланс')
    currency = models.ForeignKey('Currency', verbose_name='Валюта', on_delete=models.PROTECT)
    is_archive = models.BooleanField(verbose_name='Архивный (в разработке)', blank=True, default=False)
    
    def __str__(self):
        return f'{self.name} ({round(self.balance, 2)} {self.currency})'

    def get_absolute_url(self):
        return reverse('wallet_detail', kwargs={'pk': self.pk})
    
    def inc_balance(self, amount: float):
        """Принимает float. Увеличивает баланс кошелька. Записывает изменения в БД."""
        amount = float(amount)
        # old_balance = self.balance
        Wallet.objects.filter(pk=self.pk).update(balance=F('balance')+amount)
        # print(f'Кошелёк id={self.pk} пользователя {self.user}: '
        #       f'Баланс изменен на {amount} {self.currency}. Текущий баланс {old_balance+amount} {self.currency}')
        return amount
    
    def dec_balance(self, amount: float):
        """Принимает float. Уменьшает баланс кошелька. Записывает изменения в БД."""
        return self.inc_balance(-amount)

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ['user', '-pk']


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', blank=True)
    name = models.CharField(max_length=150, verbose_name='Название категории')
    type_of = models.CharField(max_length=10, verbose_name='Тип категории')
    is_budget = models.BooleanField(verbose_name='Бюджет вкл./выкл. (в разработке...)', blank=True, default=False)
    budget_amount = models.FloatField(verbose_name='Размер бюджета', blank=True, default=0)
    is_archive = models.BooleanField(verbose_name='Архивная категория?', blank=True, default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['user', 'pk']


class Operation(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    
    updated_at = models.DateTimeField(verbose_name='Дата и время операции')
    
    from_wallet = models.ForeignKey('Wallet',
                                    verbose_name='Счёт списания',
                                    on_delete=models.PROTECT,
                                    related_name='from_wallet',
                                    db_column='from_wallet')
    
    category = models.ForeignKey('Category',
                                 verbose_name='Категория',
                                 on_delete=models.PROTECT,
                                 db_column='category')
    
    to_wallet = models.ForeignKey('Wallet',
                                  verbose_name='Счёт получения',
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  default=None,
                                  related_name='to_wallet',
                                  null=True,
                                  db_column='to_wallet')
    
    currency1 = models.ForeignKey('Currency',
                                  verbose_name='Валюта',
                                  on_delete=models.PROTECT,
                                  related_name='currency1')
    
    amount1 = models.FloatField(verbose_name='Сумма списания')

    exchange_rate = models.FloatField(verbose_name='Курс', default=1, blank=True)
    
    currency2 = models.ForeignKey('Currency',
                                  verbose_name='Валюта платежа',
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  default=None,
                                  related_name='currency2')
    
    amount2 = models.FloatField(verbose_name='Сумма платежа')

    description = models.CharField(max_length=150, verbose_name='Описание операции', blank=True)
    
    def __str__(self):
        return f'Операция {self.pk} пользователя {self.user}'
    
    def get_absolute_url(self):
        return reverse('operation_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['-updated_at']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=30, verbose_name='Имя', blank=True)
    main_currency = models.ForeignKey('Currency', default=1, on_delete=models.PROTECT, verbose_name='Основная валюта')
    budget = models.BooleanField(blank=True, default=False, verbose_name='Режим "бюджет" (в разработке...)')

    def __str__(self):
        return f'Профиль пользователя {self.user}'

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
def create_or_update_user_profile(instance, created, **kwargs):  # kwargs нужен для декоратора
    """Если пользователь зарегистрировался - функция запускает создание для него
    дефолтных параметров, категорий, счетов. Если произошли изменения в модели User
    - то подтягивает изменения во все связанные кастомные модели"""
    if created:
        from sym_app.utils.utils import default_user_settings
        default_user_settings(instance)
    instance.profile.save()
