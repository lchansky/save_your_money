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
        self.__balance = float(balance)

    def delete(self):
        print(f'Кошелёк "{self.name}" удалён')
        return self.__balance

    def info(self):
        """Возвращает инфу о счёте в виде кортежа (name, currency, balance)"""
        return self.name, self.currency, self.__balance

    def inc_balance(self, id: int, num: float):
        """Принимает int или float. Увеличивает баланс кошелька"""
        self.__balance += float(num)
        wallets_rewrite(id, self.name, self.currency, self.__balance)
        return num

    def dec_balance(self, id: int, num: float):
        """Принимает int или float. Уменьшает баланс кошелька"""
        if self.__balance - num < 0:
            print(
                f"""Ошибка при уменьшении баланса кошелька. Недостаточно средств. 
                \r(Не хватает {num - self.__balance} {self.currency})""")
            raise ValueError('Недостаточно средств')
        else:
            self.__balance -= num
        wallets_rewrite(id, self.name, self.currency, self.__balance)
        return num

    def add_to_db(self):
        """Добавляет инфу о кошельке в CSV"""

        # Эти 2 строчки with нужны, чтобы узнать id последнего кошелька в файле
        with open('wallets.csv', encoding='UTF-8') as file:
            wallet_id = int(file.readlines()[-1].split(',')[0]) + 1

        # Запись строки кошелька с новым id в файл
        with open('wallets.csv', 'a', encoding='UTF-8') as file:
            file.write(f'\n{wallet_id},{self.name},{self.currency},{self.__balance}')

    def change_currency(self, id: int, new_currency: str):
        """Меняет валюту кошелька и переводит деньги по курсу. Вызывает wallets_rewrite() для замены записи в CSV файле
        Принимает id кошелька и новая валюта (str), возвращает новый баланс."""

        if new_currency == self.currency:  # Если новая валюта = старая валюта, то просто возвращает баланс
            return self.__balance

        try:
            exchange = currencies[f'{self.currency} {new_currency}']  # Ищет в словаре валют нужную пару
            self.__balance /= exchange
        except KeyError:
            exchange = currencies[f'{new_currency} {self.currency}']
            self.__balance *= exchange

        """
        ЕСЛИ НЕ НАШЁЛ ПАРУ 'СТАРАЯ_ВАЛЮТА НОВАЯ_ВАЛЮТА', 
        ТО ИСКАТЬ НАОБОРОТ, И НЕ ДЕЛИТЬ А УМНОЖАТЬ
        """

        self.currency = new_currency
        wallets_rewrite(id, self.name, self.currency, self.__balance)

        return self.__balance

    def change_name(self, id: int, new_name: str):
        """Меняет название кошелька. Вызывает wallets_rewrite() для замены записи в CSV файле
        Принимает id кошелька и новое название, возвращает новый баланс."""
        if new_name == self.name:  # Если новое название = старое, то ничего не происходит
            pass

        self.name = new_name
        wallets_rewrite(id, self.name, self.currency, self.__balance)


def wallets_reload():
    """Загружает данные о счетах из CSV файла. Возвращает словарь {id : Объект класса Wallet (т.е. счёт)}"""
    w = {}  # wallet
    print('\n====== Обновление данных о счетах... ==========')
    with open('wallets.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            par = i.strip().split(',')
            w[int(par[0])] = Wallet(*tuple(par[1:]))
            print(f'Счёт id: {par[0]} загружен: {w[int(par[0])].info()}')
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

    # Заменяем в строке нужную запись
    text_wallets = text_wallets.replace(text_wallets[index1:index2],
                                        f'{id},{name},{currency},{balance}')

    # Записываем обновлённую строку обратно в файл
    with open('wallets.csv', 'w', encoding='UTF-8') as file:
        file.write(text_wallets)
    print(f'Строка с id={id} успешно отредактирована!')


def currencies_reload():
    """Загружает курсы валют из CSV файла. Возвращает словарь {currency1-currency2 (str): exchange rate (float), ...}"""

    print('\n====== Обновление курсов валют... ======')
    exchange_rates = {}
    with open('currencies.csv', encoding='UTF-8') as file:
        for i in file.readlines():
            exchange_rates[i.strip().split(',')[0]] = float(i.strip().split(',')[1])
    print('====== Курсы валют обновлены! ======\n')
    return exchange_rates


# Обновляем данные о кошельках и курсах валют перед стартом программы
wallets = wallets_reload()
currencies = currencies_reload()

for i in wallets.keys():
    print(i, wallets[i].info())

wallets[7].change_currency(7, '₽')

for i in wallets.keys():
    print(i, wallets[i].info())

print('\n\n====== Конец программы ======\n\n\n')



