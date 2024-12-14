# Requests Makers

Это библиотека для удобной работы с API запросами. Из коробки вы получаете удобное кэширование и работу с запросами. Работает как в синхронном так и в асинхронном режиме (для каждого есть свой класс). Так же подключено базовое логирование.

## Базовый пример

HttpMaker и HttpMakerAsync работают при реализации своих классов на их основе. Да можно использовать их и как обычное `client = HttpMaker()` однако так делать не рекомендуется!

Создадим класс для работы с API

```python
from requests_makers import HttpMaker

class MyTestClient(HttpMaker):
    def __init__(self):
        super().__init__(
            base_url='http://your_test.url'
        )
```

Отлично! Уже на этот момент создается сессия и класс готов работать с запросами.

Представим что нам нужно получить список товаров на сайте. Для создания запросов используется метод `_make` он принимает:

- url - как полный, так и относительный (если вы при инициализации указали base_url)
- method - метод запроса ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS'). IDE подскажет вам какие принимаются аргументы.
- дополнительные параметры такие как json, data, params и headers (если потребуются).
- try_only_cache - опциональный параметр отвечающий за использование кэша если он есть (об использовании кэша будет чуть ниже).

Давайте создадим такой метод:

```python
...

class MyTestClient(HttpMaker):
    def __init__(self):
        super().__init__(
            base_url='http://your_test.url'
        )

    def get_users(self) -> list:
        users = self._make('users', 'GET', data={'auth': 'test'})
        return users.json
```

Помните что `_make` возвращает объект класс ResponseData он включает в себя:

- url - по которому делался запрос
- status - статус запроса
- json - словарь содержащий ответ. Если API возвращает НЕ json-объект в поле будет добавлен ключ 'data'.
- headers - заголовки запроса
- time - время datetime когда был сделан запрос

## Кэширование

Для создания кэша при инициализации создаем класс для работы с кэшем

```python
from requests_makers import HttpMaker, BaseCasheMaker

class MyTestClient(HttpMaker):
    def __init__(self):
        super().__init__(
            base_url='http://your_test.url',
            make_cache = True,
            cache_class = BaseCasheMaker(cache_dir = 'cache')
        )
```

BaseCasheMaker - это тестовый класс созданный лишь для понимая процесса. Дело тут в том что он просто реализует абстрактные методы CacheMaker и делает это очень "условно".

```python
class BaseCasheMaker(CacheMaker):
    def __init__(self, cache_dir: str = ''):
        super().__init__(
            cache_dir=cache_dir
        )

    def condition(self, response_data: ResponseData) -> bool:
        return True if (datetime.now() - response_data.time) <= timedelta(minutes=15) else False

    def get(self, url: str) -> ResponseData | None:
        return self._get(url)

    def put(self, response: ResponseData):
        self._put(response)

```

Если же вам нужно другое условие или необходимо больше свободы в момент создания и использования кэша. То вам нужно самим определить методы `condition` (условие когда использовать кэш), `get` (забрать из кэша) и `put` (сохранить кэш).

- condition - принимает ResponseData и должен вернуть True тогда HttpMaker должен использовать кэш или False - HttpMaker игнорирует сохраненный кэш (если он есть) и делает запрос.
- get - забрать кэш по url. Помните что это строка url запроса (для примера `your_test.url/users`) а не относительный путь к файлу с кэшем
- put - сохранить кэш

```python
class CacheMaker:
    @abstractmethod
    def condition(self, response_data: ResponseData) -> bool:
        pass
    
    @abstractmethod
    def get(self, url: str) -> ResponseData | None:
        pass

    @abstractmethod
    def put(self, response: ResponseData):
        pass
```

## Примечания по работе в асинхронном режиме

Моя библиотека отлично работает в асинхронном режиме взяв aiohttp за основу. Однако при инициализации объекта создается и сессия для работы с ним. Поэтому необходимо создавать его внутри асинхронного кода

```python
async def create_client():
    client = HttpMakerAsync()
```

Или внутри уже запущенной сессии uvicorn, django async и других.