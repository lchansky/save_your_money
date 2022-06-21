from django.db import models
import datetime as dt  # не удалять

from . import models


def default_user_settings(instance):
    """Создаёт дефолтные категории, счета и настройки для пользователя"""

    if models.Currency.objects.all().count() == 0:
        models.Currency.objects.create(name='RUB', exchange_to='RUB', exchange_rate=1, exchange_rate_reverse=1)
    
    models.Profile.objects.create(user=instance)
    
    # Создание дефолтных категорий для юзера. Оптимизированный метод
    default_categories = models.DefaultCategories.objects.all()
    if default_categories.count() == 0:
        write_default_categories_to_db()
    models.Category.objects.bulk_create(
        [models.Category(user=instance, name=i.category_name, type_of=i.category_type_of)
         for i in default_categories]
    )

    ruble = models.Currency.objects.get(pk=1)
    
    # Создание дефолтных кошельков для юзера
    default_wallets = models.DefaultWallets.objects.all()
    if default_wallets.count() == 0:
        write_default_wallets_to_db()
    for wallet in default_wallets:
        models.Wallet.objects.create(user=instance,
                                     name=wallet.wallet_name,
                                     currency=ruble)

    # Вариант с добавлением первой операции
    
    # models.Operation.objects.create(
    #     user=instance,
    #     updated_at=dt.datetime.now(),
    #     from_wallet=models.Wallet.objects.get(user=instance, name='Карта'),
    #     category=models.Category.objects.get(user=instance, name='Продукты'),
    #     currency1=..., amount1=500,
    #     currency2=..., amount2=500,
    #     description='Первая операция!')


def write_default_categories_to_db():
    categories = ({'category_type_of': 'pay', 'category_name': 'Продукты'},
                  {'category_type_of': 'pay', 'category_name': 'Кафе'},
                  {'category_type_of': 'pay', 'category_name': 'Досуг'},
                  {'category_type_of': 'pay', 'category_name': 'Транспорт'},
                  {'category_type_of': 'pay', 'category_name': 'Здоровье'},
                  {'category_type_of': 'pay', 'category_name': 'Подарки'},
                  {'category_type_of': 'pay', 'category_name': 'Семья'},
                  {'category_type_of': 'pay', 'category_name': 'Покупки'},
                  {'category_type_of': 'earn', 'category_name': 'Зарплата'},
                  {'category_type_of': 'earn', 'category_name': 'Подарки'},
                  {'category_type_of': 'transfer', 'category_name': 'Переводы'},)
    models.DefaultCategories.objects.bulk_create(
        [models.DefaultCategories(
            category_name=category['category_name'],
            category_type_of=category['category_type_of'])
         for category in categories]
    )


def write_default_wallets_to_db():
    wallets_names = ('Карта', 'Наличные')
    models.DefaultWallets.objects.bulk_create(
        [models.DefaultWallets(wallet_name=name)
         for name in wallets_names]
    )