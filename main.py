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
    def __init__(self, name='Счёт 1', currency='RUB', balance=0.00):
        """
        Присваивает кошельку свойства при создании и при извлечении его из БД.
        """
        self.__balance = float(balance)
        self.currency = currency
        self.name = name

    def __del__(self):
        print(f'Кошелёк {self.name} удалён')
        return self.__balance

    def info(self):
        """Возвращает инфу о счёте в виде кортежа (name, currency, balance)"""
        return self.name, self.currency, self.__balance

    def inc_balance(self, num: float):
        """Принимает int или float. Увеличивает баланс кошелька"""
        self.__balance += float(num)
        return num

    def dec_balance(self, num):
        if self.__balance - num < 0:
            print(
                f"""Ошибка при уменьшении баланса кошелька. Недостаточно средств. 
                \r(Не хватает {num - self.__balance} {self.currency})""")
            raise ValueError('Недостаточно средств')
        else:
            self.__balance -= num
        return num


""" Начало работы программы. Считывание всех данных из CSV файлов. """

# Загрузка кошельков в словарь
# {id : Объект класса Wallet (т.е. счёт)}

w = {}  # wallet
print('Обновление данных о счетах...')
with open('wallets.csv', encoding='UTF-8') as file:
    for i in file.readlines():
        par = i.strip().split(',')
        w[par[0]] = Wallet(*tuple(par[1:]))
        print(f'Счёт id:{par[0]} создан: {w[par[0]].info()}')
print('Данные о кошельках обновлены!')

print(w['1'].info())








print()
