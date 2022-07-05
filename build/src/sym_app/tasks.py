import json

import requests
from celery import shared_task
from google_currency import CODES, convert

from sym_app.models import Currency
import xml.etree.ElementTree as ETree

ACCUR = 1000


@shared_task
def update_currencies_db():
    print(f'====== Обновление курсов валют начато ======')

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

    print(f'====== Обновление курсов валют прошло успешно, БД обновлена, запросов гугл: {convert_count} ======')
    return True


