from django.db import models
from datetime import datetime  # не удалять

from . import models


def default_user_settings(instance):
    """Создаёт дефолтные категории, счета и настройки для пользователя"""
    
    models.Profile.objects.create(user=instance)
    
    # Создание дефолтных категорий для юзера. Оптимизированный метод
    default_categories = models.DefaultCategories.objects.all()
    models.Category.objects.bulk_create(
        [models.Category(user=instance, name=i.category_name, type_of=i.category_type_of)
         for i in default_categories]
    )
    
    # Создание дефолтных категорий для юзера. Неоптимизированный метод
    # for i in models.DefaultCategories.objects.all():
    #     models.Category.objects.create(user=instance,
    #                                    name=i.category_name,
    #                                    type_of=i.category_type_of)

    ruble = models.Currency.objects.get(pk=1)
    
    # Тут я решил не оптимизировать, т.к. 3 SQL запроса думаю нормально
    # (1 запрос на приём всех дефолтных кошельков (2 шт) и 2 запроса на создание)
    for i in models.DefaultWallets.objects.all():
        models.Wallet.objects.create(user=instance,
                                     name=i.wallet_name,
                                     currency=ruble)

    # Вариант с добавлением первой операции
    #
    # models.Operation.objects.create(
    #     user=instance,
    #     updated_at=datetime.now(),
    #     from_wallet=models.Wallet.objects.get(user=instance, name='Карта'),
    #     category=models.Category.objects.get(user=instance, name='Продукты'),
    #     currency1=..., amount1=500,
    #     currency2=..., amount2=500,
    #     description='Первая операция!')
