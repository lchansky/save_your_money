class Category:
    """Класс категорий расходов. Это контейнер для создания категорий. По умолчанию для пользователя создаётся 3 вида
    категорий: Расходы, Доходы и Переводы (между счетами)"""
    def __init__(self, name: str, type='Category'):
        """
        Присваивает категории свойства при создании или при извлечении ее из БД.
        """
        self.name = name
        self.type = type

    def change_name(self, new_name: str):
        if find_in_db(self.type, new_name) == -1:
            categories_rewrite(self.type, self.name, new_name)
            self.name = new_name
        else:
            print(f'Невозможно переименовать категорию "{self.name}". Категория "{new_name}" уже существует.')

    def get_name(self):
        return self.name

    def add_to_db(self):
        """Запись строки категории в файл"""
        if find_in_db(self.type, self.name) == -1:
            with open('categories.csv', 'a', encoding='UTF-8') as file:
                file.write(f'{self.type},{self.name}\n')
            print(f'categories.csv: Добавлена запись - {self.type},{self.name}\\n')
        else:
            print('Невозможно добавить категорию в CSV файл. Смените название категории.')

    def delete(self):
        """Удаляет категорию из CSV файла"""

        """В БУДУЩЕМ СДЕЛАТЬ, ЧТОБЫ ПРИ УДАЛЕНИИ, ВО ВСЕХ ОПЕРАЦИЯХ УДАЛЁННАЯ КАТЕГОРИЯ ПОМЕЧАЛАСЬ КАК УДАЛЁННАЯ
        С ВОЗМОЖНОСТЬЮ ПЕРЕНЕСТИ ВСЕ ОПЕРАЦИИ ИЗ УДАЛЯЕМОЙ КАТЕГОРИИ НА ОДНУ ИЗ СУШЕСТВУЮЩИХ"""

        print(f'====== Запущено удаление категории ======')

        # Читаем из CSV данные в строку
        with open('categories.csv', encoding='UTF-8') as file:
            text = file.read()

        # Находим индекс начала строки
        index1 = text.find(f'{self.type},{self.name}')
        # Находим индекс конца строки (Поиск находит первый перенос строки, начиная index1)
        index2 = index1 + len(f'{self.type},{self.name}') + 1

        # Заменяем в тексте нужную запись (строку)
        text = text.replace(text[index1:index2], '')

        # Записываем обновлённый текст обратно в файл
        with open('categories.csv', 'w', encoding='UTF-8') as file:
            file.write(text)
        print(f'\t\tcategories.csv: Категория "{self.type},{self.name}" успешно удалена!')


class Pay(Category):
    """Категория расходов, наследуется от категорий."""

    def __init__(self, name: str, type='pay'):
        """
        Присваивает категории свойства при создании или при извлечении ее из БД.
        """
        self.name = name
        self.type = type

    def delete(self):
        super(Pay, self).delete()
        pay_categories.remove(self)
        print(f'\t\tpay_categories[]: Категория "{self.type},{self.name}" успешно удалена!')


class Earn(Category):
    """Категория доходов, наследуется от категорий."""

    def __init__(self, name: str, type='earn'):
        """
        Присваивает категории свойства при создании или при извлечении ее из БД.
        """
        self.name = name
        self.type = type

    def delete(self):
        super(Earn, self).delete()
        earn_categories.remove(self)
        print(f'\t\tearn_categories[]: Категория "{self.type},{self.name}" успешно удалена!')


class Transfer(Category):
    """Категория переводов, наследуется от категорий."""
    pass


"""
Есть функция которая создаёт файл CSV и записывает туда дефолтные категории.
Если этот файл уже существует, то он читает оттуда данные и создаёт два списка, выглядящие примерно так:
pay_categories = [Объекты класса Pay], earn_categories = [Объекты класса Earn].
"""


def categories_reload():
    """Загружает данные о категориях из CSV файла. Возвращает два списка:
    pay_categories = [Объекты класса Pay], earn_categories = [Объекты класса Earn]"""

    print('\n====== Загрузка данных о категориях... ==========')
    try:
        with open('categories.csv'):
            pass
    except FileNotFoundError:
        print('\t\tФайл categories.csv не найден.')
        with open('categories.csv', 'a', encoding='UTF-8') as file:
            with open('default_categories.csv', encoding='UTF-8') as file2:
                file.write(file2.read())
        print('\t\tФайл categories.csv создан cо стандартными категориями.')

    pay_list = []
    earn_list = []

    with open('categories.csv', encoding='UTF-8') as file:
        for i in file.readlines()[1:]:
            params = i.strip().split(',')
            if params[0] == 'pay':
                pay_list.append(Pay(params[1]))
            elif params[0] == 'earn':
                earn_list.append(Earn(params[1]))
    print('\tРасходные категории:\n\t\t', [i.get_name() for i in pay_list],
          '\n\tДоходные категории:\n\t\t', [i.get_name() for i in earn_list])
    print('====== Данные о категориях загружены! ==========\n')
    return pay_list, earn_list


def categories_rewrite(type: str, name: str, new_name: str):
    """Открывает файл CSV и заменяет в нём строку с указанными параметрами 'type,name' => 'type,new_name' """

    # Читаем из CSV данные в строку
    with open('categories.csv', encoding='UTF-8') as file:
        text = file.read()

    # Находим индекс начала строки
    index1 = text.find(f'{type},{name}')
    # Находим индекс конца строки (Поиск находит первый перенос строки, начиная index1)
    index2 = index1 + len(f'{type},{name}')

    # Заменяем в тексте нужную запись (строку)
    text = text.replace(text[index1:index2], f'{type},{new_name}')

    # Записываем обновлённый текст обратно в файл
    with open('categories.csv', 'w', encoding='UTF-8') as file:
        file.write(text)
    print(f'categories.csv: Строка "{type},{name}" успешно заменена на "{type},{new_name}"!')


def find_in_db(type, request):
    """Ищет в CSV файле строку request, например 'pay,Продукты\n'. При нахождении возвращает номер строки в файле.
    Если строка не найдена, возвращает -1"""
    try:
        with open('categories.csv', encoding='UTF-8') as file:
            return file.readlines()[1:].index(f'{type},{request}\n')
    except ValueError:
        return -1


pay_categories, earn_categories = categories_reload()

pay_categories[3].delete()

print([i.get_name() for i in pay_categories],
      [i.get_name() for i in earn_categories], sep='\n')

