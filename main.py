from pprint import pprint


class Wallet:
    """
    Класс Кошелёк. Это контейнер для создания счетов. По умолчанию для каждого пользователя создаётся 1 счёт в ₽.
    Методы класса:
        увеличение и уменьшение баланса кошелька (за счёт расходов/доходов)
        открытие существующих кошельков из файла CSV
    Свойства кошелька:
        currency - валюта. Поддерживается только 3 валюты - ₽, $, €.
        name - название,
        balance - баланс.
    """
    def __init__(self, name='Счёт по умолчанию', currency='₽', balance=0.00):
        """
        Присваивает кошельку свойства при создании или при извлечении его из БД.
        """
        self.__balance = float(balance)
        self.currency = currency
        self.name = name

    def __del__(self):
        print(f'Кошелёк "{self.name}" удалён')
        return self.__balance

    def info(self):
        """Возвращает инфу о счёте в виде кортежа (name, currency, balance)"""
        return self.name, self.currency, self.__balance

    def inc_balance(self, num: float):
        """Принимает int или float. Увеличивает баланс кошелька"""
        self.__balance += float(num)
        return num

    def dec_balance(self, num: float):
        """Принимает int или float. Уменьшает баланс кошелька"""
        if self.__balance - num < 0:
            print(
                f"""Ошибка при уменьшении баланса кошелька. Недостаточно средств. 
                \r(Не хватает {num - self.__balance} {self.currency})""")
            raise ValueError('Недостаточно средств')
        else:
            self.__balance -= num
        return num

    def add_to_db(self):
        """Добавляет инфу о кошельке в CSV"""

        # Эти 2 строчки with нужны, чтобы узнать id последнего кошелька в файле
        with open('wallets.csv', encoding='UTF-8') as file:
            wallet_id = int(file.readlines()[-1].split(',')[0]) + 1

        # Запись строки кошелька с новым id в файл
        with open('wallets.csv', 'a', encoding='UTF-8') as file:
            file.write(f'\n{wallet_id},{self.name},{self.currency},{self.__balance}')

    def change_currency(self, new_currency: str):
        """Меняет валюту кошелька и переводит деньги по курсу.
        Принимает строку - новая валюта, возвращает новый баланс."""

        if new_currency == self.currency:  # Если новая валюта = старая валюта, то просто возвращает баланс
            return self.__balance

        exchange = currencies[f'{self.currency} {new_currency}']  # Ищет в словаре валют нужную пару
        self.__balance /= exchange
        return self.__balance


""" Начало работы программы. Считывание всех данных из CSV файлов. """


# Загрузка кошельков
def wallets_reload():
    """Загружает данные о счетах из CSV файла. Возвращает словарь {id : Объект класса Wallet (т.е. счёт)}"""
    w = {}  # wallet
    print('Обновление данных о счетах...')
    with open('wallets.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            par = i.strip().split(',')
            w[int(par[0])] = Wallet(*tuple(par[1:]))
            print(f'Счёт id: {par[0]} загружен: {w[int(par[0])].info()}')
    print('Данные о кошельках обновлены!')
    return w


def currencies_reload():
    """Загружает курсы валют из CSV файла. Возвращает словарь {currency1-currency2 (str): exchange rate (float), ...}"""

    print('Обновление курсов валют...')
    exchange_rates = {}
    with open('currencies.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            exchange_rates[i.strip().split(',')[0]] = float(i.strip().split(',')[1])
    print('Курсы валют обновлены!')
    return exchange_rates


# Обновляем данные о кошельках и курсах валют перед стартом программы
wallets = wallets_reload()
currencies = currencies_reload()
print(currencies)

print(wallets[2].info())
print(wallets[2].change_currency('₽'))
print(wallets[2].info())

# new_wallet = Wallet(balance='555')
# new_wallet.add_to_db()


