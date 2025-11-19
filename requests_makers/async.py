import asyncio
import logging

import aiohttp

from .single import Singleton
from .response import ResponseData, Method
from .cache import CacheMaker


class HttpMakerAsync(Singleton):
    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        cache_class: CacheMaker | None = None,
        tries_to_reconnect: int = 3,
        timeout_in_sec: int = 60,
    ):
        if base_headers is None:
            base_headers = dict()
        if base_url == '':
            self._base_url = base_url
        else:
            self._base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        self._headers = base_headers
        self._tries_to_reconnect = tries_to_reconnect
        self._timeout = timeout_in_sec
        self.cache = cache_class

    def get_full_path(self, url) -> str:
        if url == '':
            return self._base_url
        return f'{self._base_url}{url if not url.startswith('/') else url[1:]}'

    async def __execute(
        self,
        url: str,
        method: Method,
        data: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData | None:
        logging.debug(
            f'{self.__class__.__name__} {method} -> {url} ? {params}',
        )
        for _ in range(self._tries_to_reconnect):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session:
                    http_method = getattr(session, method.lower())
                    if headers is None:
                        headers = {}
                    headers.update(self._headers)
                    async with http_method(
                        url=self.get_full_path(url),
                        headers=headers,
                        data=data,
                        json=json,
                        params=params
                    ) as res:
                        return await self.__get_response_data(res)
            except aiohttp.ClientConnectorError as e:
                logging.error(f'{self.__class__.__name__} > Client connection error {e}')
                if try_wait_if_error:
                    await asyncio.sleep(10)
                    continue
                return None
            except aiohttp.ConnectionTimeoutError as e:
                logging.error(f'{self.__class__.__name__} > Connection error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(20)
                    continue
                return None
            except aiohttp.ClientError as e:
                logging.critical(f'{self.__class__.__name__} > Client error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(60)
                    continue
                return None
            except AttributeError as e:
                logging.critical(f'{self.__class__.__name__} > Uncaught error: {e}')
                return None
        logging.critical(f'{self.__class__.__name__} > Tries out but no return')

    async def _make(
        self,
        url: str = '',
        method: Method = 'GET',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_only_cache: bool = False,
        try_wait_if_error: bool = True,
    ) -> ResponseData | None:
        logging.debug(f'{self.__class__.__name__} > make -> {self.get_full_path(url)}\n')
        if self.cache is not None:
            # ! Пытаемся получить кэш по url
            cache_data = self.cache.get(self.get_full_path(url))
            if cache_data is not None:
                # ? Если возвращать только кэш или выполняется условие кэша
                if try_only_cache or self.cache.condition(cache_data):
                    logging.debug(f'{self.__class__.__name__} > get cache > {url}')
                    return cache_data

        res = await self.__execute(
            url=url,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
        )

        if self.cache is not None and res is not None:
            # ! Сохраняем кэш
            self.cache.put(res)
        return res

    @staticmethod
    async def __get_response_data(
        response: aiohttp.ClientResponse,
    ) -> ResponseData | None:
        # Получаем тип контента (проверяем оба варианта регистра)
        try:
            content_type = (
                response.headers.get('Content-Type') or
                {name.lower(): val for name, val in response.headers}.get('content-type')
            )
        except ValueError:
            logging.debug(f'HttpMakerAsync > No content type > set empty', 'warning')
            content_type = 'empty'

        try:
            match content_type.split(';')[0].strip().lower():
                case 'application/json' | 'text/html':
                    data = await response.json(content_type=None if 'html' in content_type else 'json')
                    if type(data) is not dict:
                        data = {'data': data}
                case 'empty':
                    data = await response.json(content_type='json')
                case _:
                    logging.debug(f'Unreadable content type: {content_type}', 'warning')
                    return None
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=dict(response.headers),
                json=data,
            )
        except aiohttp.ContentTypeError as e:
            logging.error(e)
            return None
