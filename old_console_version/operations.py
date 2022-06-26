from datetime import datetime
from pprint import pprint


def read_from_db(date_from='01.01.0001', date_to='01.01.3000'):
    """Принимает период времени в виде двух строк в формате dd.mm.yyyy.
    Возвращает список операций, которые входят в этот промежуток, в виде словаря {id: [operation_params]}"""
    date_from = datetime.strptime(date_from, '%d.%m.%Y')
    date_to = datetime.strptime(date_to, '%d.%m.%Y')
    print(date_from, 'to', date_to)
    if date_from > date_to:
        print('Ошибка! Дата начала периода должна быть <= дате конца периода!')
    with open('operations.csv', encoding='UTF-8') as file:
        oper_dict = {}
        for line in file.readlines()[1:]:
            text = line.strip().split('"')
            operation = [param for param in text[3::2]]
            if date_from <= datetime.strptime(operation[0], '%d.%m.%Y') <= date_to:
                oper_dict[int(text[1])] = operation
        return(oper_dict)


operations = read_from_db('11.04.2022', '11.04.2022')
pprint(operations)

