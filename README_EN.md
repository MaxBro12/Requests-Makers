# Requests Makers

This is a library for convenient work with API requests. Out of the box you get convenient caching and work with requests. Works both in synchronous and asynchronous mode (there is a class for each). Basic logging is also connected.

## Basic example

HttpMaker and HttpMakerAsync work when implementing their classes based on them. Yes, you can use them as a regular `client = HttpMaker()`, but this is not recommended!

Let's create a class for working with API

```python
from requests_makers import HttpMaker

class MyTestClient(HttpMaker):
    def __init__(self):
        super().__init__(
            base_url='http://your_test.url'
        )
```

Great! At this point, a session is already created and the class is ready to work with requests.

Let's imagine that we need to get a list of products on the site. The `_make` method is used to create requests. It accepts:

- url - both full and relative (if you specified base_url during initialization)
- method - request method ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS'). The IDE will tell you what arguments are accepted.
- additional parameters such as json, data, params and headers (if required).
- try_only_cache - optional parameter responsible for using the cache if there is one (we will talk about using the cache below).

Let's create such a method:

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

Remember that `_make` returns a ResponseData class object, it includes:

- url - the request was made to
- status - the request status
- json - a dictionary containing the response. If the API does NOT return a json object, the 'data' key will be added to the field.
- headers - request headers
- time - datetime when the request was made

## Caching

To create a cache during initialization, we create a class for working with the cache

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

BaseCasheMaker is a test class created only for understanding the process. The point here is that it simply implements abstract methods of CacheMaker and does it very "simply".

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

If you need another condition or need more freedom when creating and using the cache. Then you need to define the methods `condition` (condition when to use the cache), `get` (take from the cache) and `put` (save the cache) yourself.

- condition - accepts ResponseData and should return True then HttpMaker should use cache or False - HttpMaker ignores saved cache (if any) and makes a request.
- get - get cache by url. Remember that this is the request url string (for example `your_test.url/users`) and not a relative path to the file with cache
- put - save cache

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

## Notes on working in asynchronous mode

My library works great in asynchronous mode taking aiohttp as a basis. However, when an object is initialized, a session is also created to work with it. Therefore, it is necessary to create it inside asynchronous code

```python
async def create_client():
    client = HttpMakerAsync()
```

Or inside an already running session uvicorn, django async and others.