from pprint import pprint
from functools import wraps

class Wallet:
    """
    Класс Кошелёк. Это контейнер для создания счетов. По умолчанию для каждого пользователя создаётся 1 счёт в ₽.
    Методы класса:
        увеличение и уменьшение баланса кошелька (за счёт расходов/доходов)
        открытие существующих кошельков из файла CSV
    Свойства кошелька:
        name - название,
        currency - валюта. Поддерживается только 3 валюты - '₽', '$', '€'.
        balance - баланс float.
    """

    def __init__(self, name='Счёт по умолчанию', currency='₽', balance=0.00):
        """
        Присваивает кошельку свойства при создании или при извлечении его из БД.
        """
        self.name = name
        self.currency = currency
        self._balance = float(balance)

    def info(self):
        """Возвращает инфу о счёте в виде кортежа (name, currency, balance)"""
        return self.name, self.currency, self._balance

    def get_currency(self):
        """Возвращает валюту счёта (currency: str)"""
        return self.currency

    def inc_balance(self, id: int, amount: float):
        """Принимает int или float. Увеличивает баланс кошелька. Записывает изменения в CSV файл."""
        amount = float(amount)
        self._balance += amount
        wallets_rewrite(id, self.name, self.currency, self._balance)
        print(f'Кошелёк id={id}: Баланс увеличен на {amount} ({self._balance-amount} ===>>> {self._balance})')
        return amount

    def dec_balance(self, id: int, amount: float):
        """Принимает int или float. Уменьшает баланс кошелька. Записывает изменения в CSV файл."""
        amount = float(amount)
        if self._balance - amount < 0:
            print(
                f"""Кошелёк id={id}: Ошибка при уменьшении баланса кошелька - недостаточно средств. 
                \r(Не хватает {amount - self._balance} {self.currency})""")
            raise ValueError('Недостаточно средств')
        else:
            self._balance -= amount
        wallets_rewrite(id, self.name, self.currency, self._balance)
        print(f'Кошелёк id={id}: Баланс уменьшен на {amount} ({self._balance+amount} ===>>> {self._balance})')
        return amount

    def add_to_db(self):
        """Добавляет инфу о кошельке в CSV"""

        # Эти 2 строчки with нужны, чтобы узнать id последнего кошелька в файле
        with open('wallets.csv', encoding='UTF-8') as file:
            wallet_id = int(file.readlines()[-1].split(',')[0]) + 1

        # Запись строки кошелька с новым id в файл
        with open('wallets.csv', 'a', encoding='UTF-8') as file:
            file.write(f'{wallet_id},{self.name},{self.currency},{self._balance}\n')
        print(f'wallets.csv: Добавлена запись - {wallet_id},{self.name},{self.currency},{self._balance}\\n')

    def delete(self, id: int, id2=-1):
        """Удаляет кошелёк id из CSV файла, переводит деньги на кошелёк id2 (по умолчанию деньги уничтожаются)"""

        print(f'====== Запущено удаление кошелька id={id} ======')

        # Переводим деньги на другой кошелёк, если таковой указан
        if id2 > 0:
            print(f'=== Перенос денег с id={id} на id={id2} начат ===')
            transfer_funds(self._balance, id, id2)
            print(f'=== Перенос денег с id={id} на id={id2} завершён ===')

        # Читаем из CSV данные в строку
        with open('wallets.csv', encoding='UTF-8') as file:
            text_wallets = file.read()

        # Находим индекс начала строки по id
        index1 = text_wallets.find(f'\n{id},')
        # Находим индекс конца строки (Поиск находит первый перенос строки, начиная index1)
        index2 = text_wallets.find('\n', index1 + 1)

        # Удаляем строку
        text_wallets = text_wallets.replace(text_wallets[index1:index2], '')

        # Записываем обновлённый текст обратно в файл
        with open('wallets.csv', 'w', encoding='UTF-8') as file:
            file.write(text_wallets)
        print(f'wallets.csv: Удалена запись - \\n{id},{self.name},{self.currency},{self._balance}')

        wallets.pop(id)
        print(f'Кошелёк id={id}: Удалён из словаря')
        print(f'====== Кошелёк id={id} удалён успешно======')

    def change_currency(self, id: int, new_currency: str):
        """Меняет валюту кошелька и переводит деньги по курсу. Вызывает wallets_rewrite() для замены записи в CSV файле
        Принимает id кошелька и новая валюта (str), возвращает новый баланс."""

        if new_currency == self.currency:  # Если новая валюта = старая валюта, то просто возвращает баланс
            return self._balance

        self._balance = exchanger(self._balance, self.currency, new_currency)
        print(f'Кошелёк id={id}: Валюта изменена ({self.currency} => {new_currency}). Новый баланс: {self._balance}')
        self.currency = new_currency
        wallets_rewrite(id, self.name, self.currency, self._balance)

        return self._balance

    def change_name(self, id: int, new_name: str):
        """Меняет название кошелька. Вызывает wallets_rewrite() для замены записи в CSV файле
        Принимает id кошелька и новое название, возвращает новый баланс."""
        if new_name == self.name:  # Если новое название = старое, то ничего не происходит
            pass
        print(f'Кошелёк id={id}: Изменено название ("' + self.name + '" ===>>> "' + new_name + '")')
        self.name = new_name
        wallets_rewrite(id, self.name, self.currency, self._balance)


def wallets_reload():
    """Загружает данные о счетах из CSV файла. Возвращает словарь {id : Объект класса Wallet (т.е. счёт)}"""
    w = {}  # wallet
    print('\n====== Обновление данных о счетах... ==========')
    with open('wallets.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            params = i.strip().split(',')
            w[int(params[0])] = Wallet(*tuple(params[1:]))
            print(f'Счёт id: {params[0]} загружен: {w[int(params[0])].info()}')
    print('====== Данные о кошельках обновлены! ==========\n')
    return w


def wallets_rewrite(id: int, name: str, currency: str, balance: float):
    """Открывает файл CSV и заменяет в нём 1 строку с указанными параметрами"""

    # Читаем из CSV данные в строку
    with open('wallets.csv', encoding='UTF-8') as file:
        text_wallets = file.read()

    # Находим индекс начала строки по id
    index1 = text_wallets.find(f'\n{id},') + 1
    # Находим индекс конца строки (Поиск находит первый перенос строки, начиная index1)
    index2 = text_wallets.find('\n', index1)

    # Заменяем в тексте нужную запись (строку)
    text_wallets = text_wallets.replace(text_wallets[index1:index2], f'{id},{name},{currency},{balance}')

    # Записываем обновлённый текст обратно в файл
    with open('wallets.csv', 'w', encoding='UTF-8') as file:
        file.write(text_wallets)
    print(f'wallets.csv: Строка с id={id} успешно отредактирована!')


def currencies_reload():
    """Загружает курсы валют из CSV файла. Возвращает словарь {currency1-currency2 (str): exchange rate (float), ...}"""

    print('\n====== Обновление курсов валют... ======')
    exchange_rates = {}
    with open('currencies.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            exchange_rates[i.strip().split(',')[0]] = float(i.strip().split(',')[1])
    print('====== Курсы валют обновлены! ======\n')
    return exchange_rates


def exchanger(amount: float, currency_from: str, currency_to: str):
    """
    Принимает сумму денег amount в валюте currency_from, меняет её по курсу и возвращает сумму денег в валюте currency_to
    """
    if currency_from == currency_to:
        return amount
    try:
        exchange = currencies[f'{currency_from} {currency_to}']  # Ищет в словаре валют нужную пару
        return amount / exchange
    except KeyError:
        exchange = currencies[f'{currency_to} {currency_from}']  # Если такого ключа в словаре валют нет, ищет наоборот
        return amount * exchange


def transfer_funds(amount: float, id_from: int, id_to: int):
    """Отправляет деньги с кошелька id_from сумму num на кошелёк id_to.
    Используется валюта кошелька id_from. Если валюты разные, осуществляется обмен по курсу и затем перевод.
    После выполнения перевода обновляет данные о кошельках в CSV файле."""

    if amount <= 0:
        print('Ошибка при переводе средств. Сумма перевода не может быть меньше или равна нулю. Ваша сумма:', amount)
        return None

    # Уменьшение баланса счёта-отправителя
    wallets[id_from].dec_balance(id_from, amount)

    # Перевод суммы трансфера в валюту счёта-получателя
    new_amount = exchanger(amount, wallets[id_from].get_currency(), wallets[id_to].get_currency())

    # Увеличение баланса счёта-получателя
    wallets[id_to].inc_balance(id_to, new_amount)

    print(f'Кошелёк id={id_from}: Деньги успешно переведены на кошелёк id={id_to}')


# Обновляем данные о кошельках и курсах валют перед стартом программы
wallets = wallets_reload()
currencies = currencies_reload()

# for i in wallets.keys():
#     print(i, wallets[i].info())
# print()

