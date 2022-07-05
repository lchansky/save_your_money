import json
import datetime as dt  # не удалять

from google_currency import convert, CODES
import json

from sym_app.models import *


def default_user_settings(instance):
    """Создаёт дефолтные категории, счета и настройки для пользователя"""

    if Currency.objects.all().count() == 0:
        Currency.objects.create(name='RUB', exchange_to='RUB', exchange_rate=1, exchange_rate_reverse=1)
        Currency.objects.create(name='USD', exchange_to='RUB', exchange_rate=55, exchange_rate_reverse=1/55)
        Currency.objects.create(name='EUR', exchange_to='RUB', exchange_rate=58, exchange_rate_reverse=1/58)
    
    Profile.objects.create(user=instance)
    
    # Создание дефолтных категорий для юзера. Оптимизированный метод
    default_categories = DefaultCategories.objects.all()
    if default_categories.count() == 0:
        write_default_categories_to_db()
    Category.objects.bulk_create(
        [Category(user=instance, name=i.category_name, type_of=i.category_type_of)
         for i in default_categories]
    )

    ruble = Currency.objects.get(pk=1)
    
    # Создание дефолтных кошельков для юзера
    default_wallets = DefaultWallets.objects.all()
    if default_wallets.count() == 0:
        write_default_wallets_to_db()
    for wallet in default_wallets:
        Wallet.objects.create(user=instance,
                              name=wallet.wallet_name,
                              currency=ruble)

    # Вариант с добавлением первой операции
    
    # Operation.objects.create(
    #     user=instance,
    #     updated_at=dt.datetime.now(),
    #     from_wallet=Wallet.objects.get(user=instance, name='Карта'),
    #     category=Category.objects.get(user=instance, name='Продукты'),
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
    DefaultCategories.objects.bulk_create(
        [DefaultCategories(
            category_name=category['category_name'],
            category_type_of=category['category_type_of'])
         for category in categories]
    )


def write_default_wallets_to_db():
    wallets_names = ('Карта', 'Наличные')
    DefaultWallets.objects.bulk_create(
        [DefaultWallets(wallet_name=name)
         for name in wallets_names]
    )


def universal_context(request):
    """Принимает запрос и контекст, добавляет к контексту те переменные,
    которые используются на каждой странице.
    Например, на navbar используется"""
    wallets = Wallet.objects.filter(user=request.user).select_related('currency')
    optional_name = Profile.objects.get(user=request.user).name
    main_currency = Profile.objects.get(user=request.user).main_currency
    overall_balance = 0
    for item in list(wallets.values('balance', 'currency')):
        overall_balance += exchanger(item['currency'], main_currency.pk, item['balance'])
    
    context = {
        'optional_name': optional_name,
        'wallets': wallets,
        'main_currency': main_currency,
        'overall_balance': round(overall_balance),
    }
    return context


def load_exchange_rates_pks():
    with open('exchange_rates_pks.json', 'r') as file:
        exchange_rates_pks = file.read()
    return exchange_rates_pks


def load_wallets_currencies(request):
    wallets_currency_dict = {wallet.pk: wallet.currency.pk
                             for wallet in Wallet.objects.filter(user=request.user).select_related('currency')}
    return wallets_currency_dict


def exchanger(curr1_pk, curr2_pk, amount):
    if curr1_pk == curr2_pk:
        return amount
    rates = json.loads(load_exchange_rates_pks())
    curr1_pk = str(curr1_pk)
    curr2_pk = str(curr2_pk)
    result = amount / rates[curr1_pk][curr2_pk]
    return result


# 1000 для точности, больше знаков после запятой
ACCUR = 1000




def write_currencies_to_json():
    currencies = Currency.objects.all()
    convert_count = 0
    exchange = {}
    exchange_pks = {}
    for outer in currencies:
        exchange[outer.name] = {}
        exchange_pks[outer.pk] = {}
        if outer.name in CODES.keys():
            for inner in currencies.exclude(pk=outer.pk):
                if inner.name in CODES.keys():
                    converted = json.loads(convert(inner.name, outer.name, ACCUR))
                    convert_count += 1
                    rate = float(converted.get('amount'))
                    exchange[outer.name][inner.name] = rate / ACCUR
                    exchange_pks[outer.pk][inner.pk] = rate / ACCUR

                # Блок чисто для рубля ПМР и др. валют которых нет в гугле
                # У таких валют значение "exchange_to" обязательно
                # должно быть среди валют гугла, иначе не сработает
                elif inner.exchange_to in CODES.keys():
                    converted = json.loads(convert(inner.exchange_to, outer.name, ACCUR))
                    convert_count += 1
                    rate = float(converted.get('amount'))
                    exchange[outer.name][inner.name] = rate / ACCUR * inner.exchange_rate
                    exchange_pks[outer.pk][inner.pk] = rate / ACCUR * inner.exchange_rate

        # Это тоже чисто для валют, которых нет в гугле
        elif outer.exchange_to in CODES.keys():
            for inner in currencies.exclude(pk=outer.pk):
                if inner.name in CODES.keys():
                    converted = json.loads(convert(inner.name, outer.exchange_to, ACCUR))
                    convert_count += 1
                    rate = float(converted.get('amount'))
                    exchange[outer.name][inner.name] = rate / ACCUR / outer.exchange_rate
                    exchange_pks[outer.pk][inner.pk] = rate / ACCUR / outer.exchange_rate

    with open('exchange_rates.json', 'w') as file:
        json.dump(exchange, file)
    with open('exchange_rates_pks.json', 'w') as file:
        json.dump(exchange_pks, file)

    print(f'====== Загрузка курсов валют прошла успешно, JSON файл обновлен, запросов гугл: {convert_count} ======')
