import json

import requests
from celery import shared_task
from google_currency import CODES, convert

from sym_app.models import Currency
import xml.etree.ElementTree as ETree

ACCUR = 1000  # Для точности, больше знаков после запятой


@shared_task
def update_currencies_db():
    print(f'====== Started updating currencies rates... ======')

    currencies = Currency.objects.all()
    convert_count = 0

    # Блок парсинга курса Рубля ПМР
    rup = Currency.objects.get(name='RUP')
    response = requests.get("https://www.agroprombank.com/xmlinformer.php")
    root = ETree.fromstring(response.text)
    rup_rate = float(root[1][2].findtext('currencySell'))
    rup.exchange_rate = 1 / rup_rate
    rup.exchange_rate_reverse = rup_rate
    rup.save()

    # Блок парсинга всех остальных валют
    for currency in currencies:  # берём по одной валюте из БД
        if currency.name in CODES.keys() and currency.exchange_to in CODES.keys():
            converted = json.loads(convert(currency.name, currency.exchange_to, ACCUR))
            convert_count += 1
            currency.exchange_rate = float(converted['amount']) / ACCUR
            currency.exchange_rate_reverse = ACCUR / float(converted['amount'])
            currency.save()

    print(f'====== Updating currencies rates has been successfully completed, DB has been updated ======')
    print(f'====== Number of requests to google: {convert_count} ======')
    return True


@shared_task
def write_currencies_to_json():
    print(f'====== Loading rates to JSON files ======')

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

    print(f'====== Loading rates to JSON files has been successfully completed ======')
    print(f'====== Number of requests to google: {convert_count} ======')


