# save_your_money
Веб-приложение для эффективного сбережения средств

Сегодня 4 апреля 2022. Прошёл примерно месяц с начала обучения Python, и я готов пробовать написать собственный резюме-проект 
для устройства на первую работу в роли Джуниор Пайтон разработчика. Погнали!

**Название приложения:**    Save Your Money!

**Описание:**               Веб-сайт, который поможет вам сохранить ваши деньги! Приложение покажет вам, на что на самом деле 
                        вы тратите деньги и поможет внедрить в жизнь привычку сбережения!

**Разделы приложения:** 
1) Счета
2) Категории расходов и доходов
3) Список трат
4) Анализ расходов и доходов
5) *Бюджет
6) Настройки
*категория изначально отключена в настройках
P.S. На любом из разделов сверху будут присутствовать кнопки "Расход", "Доход", по нажатию на которые будет переносить на страницу добавления расхода/дохода.

_1) Счета:_
        Тут будут храниться все ваши счета, также можно будет посмотреть актуальный баланс, изменить название и валюту, 
        перевести деньги между счетами, создать, архивировать или удалить счёт.
        
_2) Категории расходов и доходов:_
        Предустановлены определённые категории: Расходы: Продукты, Кафе, Досуг, Транспорт, Здоровье, Подарки, Семья, Покупки.
                                                Доходы:  Зарплата, Подарки.
                                                Переводы - здесь будут записываться переводы с одного счёта на другой.
        Есть возможность кастомизировать категории: Добавлять новые, удалять, изменять название и иконки.
        Также можно добавлять подкатегории.
        
_3) Список трат:_
        Здесь будут отображаться расходы за текущий месяц. Также можно отобразить расходы в прошлом месяце, за день, за неделю, за год и выставить свой интервал.
        Здесь же будут отображаться запланированные операции (только по 1 шт.; Например, чтобы не было 12 операций, если выбирается интервал 1 год)
        Также можно редактировать операции и удалять.
        Делать разбивку по дням или нет - хз (Т.е. если выбираешь интервал >= 2 дня, то каждый день выделяется от остальных (см. 1Money "Операции")
        
_4) Анализ расходов и доходов:_
        Здесь можно будет указать интервал и увидеть статистику по каждой категории, графики и сравнение (например: В этом месяце вы потратили на еду 200 $, 
        а в прошлом месяце - 350 $)
        
_5) Бюджет:_
        В этом разделе можно установить лимит на траты. Конечно, приложение не сможет запретить вам тратить и добавлять операции сверх лимита, но оно будет
        всячески напоминать о проблеме перерасхода, если она будет.

_6) Настройки:_
        -Изменение пароля
        -Выйти из аккаунта
        -Вкл./откл. бюджет
        -Настройка курсов валют
        -Настройки уведомлений на почту, тг бот и т.д. (ежедневные уведомления, еженедельные и -месячные отчёты, советы)
        -Настройка основной валюты, в которой отображается аналитика по счетам, и в которой создаются новые счета
        -Удалить аккаунт


**Мини-функции:**
-Платная версия (Придумать ограничения для бесплатной. Придумать как покупать/получать и применить лицензию)
-Телеграм бот или на почту: Напоминания о платежах, еженедельный/месячный отчёт, советы по сбережениям, напоминания о заполнении расходов
-Планирование операций
-Различные варнинги о превышении бюджета или приближении к лимиту.
-Экспорт данных в XSLX, PDF.
-Построение графиков и диаграмм расходов.


**За кулисами:**
-Классы для Пользователей, Счетов и Категорий
-SQL для авторизации юзеров, списка трат, счетов, категорий, настроек. Возможно для настроек можно юзать текстовый файл или csv.
-Парсинг актуальных курсов валют для обмена
-Система авторизации, чтобы у каждого пользователя отображались только его кошельки
-Удаление категории на выбор 2-мя способами: 1) Категория удаляется из списка категорий и становится "скрытой". Для каждой операции по этой категории в истории будет написано "Удалённая категория". 2) Категория переносится в список "Архивные" и операции в истории будут отображаться например так: "Авто (Архивная категория)"
-По такой же логике удаление счёта.


**В идеале сделать:**
-Разбивку по дням (Т.е. если выбираешь интервал >= 2 дня, то каждый день выделяется от остальных (см. 1Money "Операции")
-Полностью работа через телеграм бота
-Возможность прикреплять фото чеков к операциям.
-Раздел FAQ с видео-гайдами
-Регистрация с кодом на почту. И восстановление пароля.
-Авторизация через Google

**План разработки: (в процессе разработки будет описываться подробнее)**

Период: 4 апреля 2022 - 15 мая 2022.

Список дел:
    Построить основную структуру программы, без использования веба.
    Прикрутить Джанго к существующим алгоритмам.
    Выкатить сайт на хостинг
    
Список советов:
    Сэкономил - значит заработал! Рекомендуем устанавливать бюджет, чтобы легче избавляться от ненужных трат!
    

