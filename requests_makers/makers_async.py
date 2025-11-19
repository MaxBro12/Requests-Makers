import aiohttp
import asyncio
from .debug_log import create_log
from .cache import CacheMaker, BaseCacheMaker
from .exceptions import RequestMethodNotFoundException
from .response import ResponseData, Method
from .makers_single import Singleton


class HttpMakerAsync(Singleton):
    __session: aiohttp.ClientSession

    def __init__(
        self,
        base_url: str = '',
        headers: dict | None = None,
        make_cache: bool = False,
        cache_class: CacheMaker | None = None
    ):
        self._base_url = base_url
        self._headers = headers

        # Настройка кэша
        self.make_cache = make_cache
        self.cache = cache_class

        # ! Создаем сессию
        self.__session = aiohttp.ClientSession(base_url=base_url, headers=headers)
        # Если инициализировать класс до асинхронного кода вылетит ошибка создания сессии

    def __del__(self):
        self.close_session_sync()

    def close_session_sync(self):
        if not self.__session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop is not None:
                    asyncio.ensure_future(self.close_session(), loop=loop)
                else:
                    asyncio.run(self.close_session())
            except RuntimeError:
                asyncio.run(self.close_session())

    async def close_session(self):
        await self.__session.close()
        create_log(f'{type(self).__name__} > session closed', 'info')

    def get_full_path(self, url: str) -> str:
        return f'{self.__session._base_url}/{url}'

    async def _make(
            self,
            url: str,
            method: Method,
            data: dict | None = None,
            json: dict | None = None,
            params: dict | None = None,
            headers: dict | None = None,
            try_only_cache: bool = False
    ) -> ResponseData | None:
        try:
            res = None

            if self.cache is not None:
                # ! Пытаемся получить кэш по url
                cache_data = self.cache.get(self.get_full_path(url))
                if cache_data is not None:
                    # ? Если возвращать только кэш
                    if try_only_cache:
                        return cache_data

                    # ? Если выполняется условие кэша
                    if self.cache.condition(cache_data):
                        return cache_data

            res = None

            match method.upper():
                case 'GET':
                    res = await self.__session.get(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'POST':
                    res = await self.__session.post(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'PUT':
                    res = await self.__session.put(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'DELETE':
                    res = await self.__session.delete(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'HEAD':
                    res = await self.__session.head(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'OPTIONS':
                    res = await self.__session.options(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'PATCH':
                    res = await self.__session.patch(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
            if res is None:
                raise RequestMethodNotFoundException(method)

            res = await self.__get_response_data(res)

            if self.cache is not None:
                # ! Сохраняем кэш
                if self.make_cache:
                    self.cache.put(res)

            return res

        except aiohttp.ClientConnectorError:
            return None

    @staticmethod
    async def __get_response_data(response: aiohttp.ClientResponse) -> ResponseData:
        try:
            data = await response.json()
            if type(data) is not dict:
                data = {'data': data}
        except aiohttp.ContentTypeError as e:
            create_log(e, 'error')
            data = {'error': await response.text()}
        return ResponseData(
            url=response.url,
            status=response.status,
            headers=response.headers,
            json=data,
        )
