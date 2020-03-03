# Запуск
Прогнать тесты можно через `docker-compose run test`
Запустить сервер можно через `docker-compose up prod`. Серевер будет доступен на порту 8080.
# Интерфейс

Все урлы кроме `sign_in` и `login` требуют авторизации по токену. Для авторизации надо добавить заголовок
`'Authorization': 'Token <tokendata>'`

### Создать пользователя
```
POST /sign_in/ {'username': 'alex', 'password': '1'}
Response: 201
```

### Получить токен
```
POST /login/ {'username': 'alex', 'password': '1'}
Response: 200 {'token': "123"}
```

### Проверить свои кошельки
Возвращает все объекты Account привязанные к пользователю.
Пагинации в этой ручке нет, т.к. предполагается, что у пользователя нет сотни аккаунтов.
```
GET /check_balance/`
Response: 200 
{
  'result': [
    {
      'currency': 'USD',
      'description': 'USA United States Dollar',
      'amount': '100.00',
      'id': 35
    },
    {
      'currency': 'EUR',
      'description': 'European Euro',
      'amount': '0.00',
      'id': 36
    },
    {
      'currency': 'CNY',
      'description': 'Chinese Yuán',
      'amount': '0.00',
      'id': 37
    }
  ]
}
```
### Cелать перевод
Валюта перевода - валюта счета получателя.
В сеттингах есть параметр IMMEDIATELY_RATE.
Если он выставлен в False, то `taxes` и `exchange` будут просчитаны асинхронно при выполнении перевода,
и значения в ответе ручки могут быть неполными.
```
POST /request-transaction/
JSON {'source': <Account-id>, 'destination': <Account-id>, 'amount': 10}
Response: 200
{
  'result': {
    'id': 2,
    'source': 35,
    'destination': 39,
    'amount': '10.00',
    'currency': 'EUR',
    'created_at': '2020-03-03T06:14:06.455972Z',
    'processed_at': None,
    'status': 'scheduled',
    'taxes': '0.00',
    'exchange': [
      {
        'source': 'USD',
        'destination': 'EUR',
        'rate': '0.91',
        'time': '2020-03-03T06:08:24.196254Z'
      }
    ],
    'spent': '0.00'
  }
}
```
### Получить историю входящих переводов
```
GET /incoming/
Response 200
{
  'count': 1,
  'next': None,
  'previous': None,
  'results': [{
    'id': 1,
     'source': 5,
     'destination': 9,
     'amount': '10.00',
     'currency': 'EUR',
     'created_at': '2020-03-03T06:27:22.630237Z',
     'processed_at': '2020-03-03T06:27:22.687152Z'
  }]
}
```
Эта ручка возвращает только успешно завершенные транзакции. В этой ручке есть пагинация(10 на странице), фильтрация и сортировка. 
Пример сотрировки:
`GET /incoming/?ordering=created_at`
Допустимые поля для сортировки: `created_at`, `processed_at`, `source`, `amount`
Пример фильтрации:
`GET /incoming/?ordering=created_at&spent__gt=2&destination=3`
Допустимые поля для фильтрации: `created_at`, `processed_at`, `source`, `amount`
Для `created_at`, `processed_at` и `amount` доступны модификаторы: `__gt`, `__lt`, `__gte`, `__lte`

### Получить историю исходящих переводов
```
GET /outgoing/
Response 200
{
  'count': 1,
  'next': None,
  'previous': None,
  'results': [{
    'id': 1,
    'source': 5,
    'destination': 9,
    'amount': '10.00',
    'currency': 'EUR',
    'created_at': '2020-03-03T06:27:22.630237Z',
    'processed_at': '2020-03-03T06:27:22.687152Z',
    'status': 'completed',
    'taxes': '1.00',
    'exchange': [{
      'source': 'USD',
      'destination': 'EUR',
      'rate': '0.91',
      'time': '2020-03-03T06:25:27.589129Z'
    }],
    'spent': '10.01'
  }]
}
```
Эта ручка возвращает транцакии во всех статусах. В этой ручке есть пагинация(10 на странице), фильтрация и сортировка.
__Разница между spent и amount:__ spent - валюта отправителя(потрачено на перевод + налоги), amount - валюта получателя.
Пример сотрировки:
`GET /outgoing/?ordering=created_at`
Допустимые поля для сортировки: `created_at`, `processed_at`, `source`, `amount`, `spent`
Пример фильтрации:
`GET /outgoing/?ordering=created_at&spent__gt=2&destination=3`
Допустимые поля для фильтрации: `created_at`, `processed_at`, `destination`, `amount`, `status`, `currency`, `spent`
Для `created_at`, `processed_at` и `amount` доступны модификаторы: `__gt`, `__lt`, `__gte`, `__lte`
Для `status` и `currency` доступен модификатор `__in`

# Налоги
Для каждой валюты заводится отдельный налоговый счет. Получить его в консоли можно через
`Account.objects.get(type=Account.types.TAXES_ACCOUNT, currency__slug='USD')`
Раз в пять минут запускается таска `collect_taxes_for_currency`, которая собирает налоги со всех завершенных транзакций и пополняет эти счета.
Размер налогов можно изменить через админку через параметр `constance` - `TAXES`

# Обмен валют
Модель `ExchangeRate` описывает курс валют в конкретный период времени.
При запросе транзакии или обработки ее(в зависимости от флага IMMEDIATELY_RATE) производится перевод по наиболее актуальному курсу.
Старые курсы хранятся, что бы показывать в истории транзакций что как было переведено. Если валюту A нельзя перевести в B напрямую, то перевод будет осуществлятся в 2 этапа.
1) перевод А в базовую валюту
2) перевод базовой в Б
Количество переводов так же видно в истории. Базовая валюта затается настройкой BASE_CURRENCY
