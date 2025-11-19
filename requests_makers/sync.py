import logging
import requests
import time

from .single import Singleton
from .response import ResponseData, Method
from .exceptions import RequestMethodNotFoundException
from .cache import CacheMaker


class HttpMaker(Singleton):
    def __init__(
        self,
        base_url: str = '',
        headers = None | dict,
        cache_class: CacheMaker | None = None,
        tries_to_reconnect: int = 3,
        timeout_in_sec: int = 60,
    ):
        if headers is None:
            headers = dict()
        self._base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        self.headers = headers
        self._tries_to_reconnect = tries_to_reconnect
        self.cache = cache_class
        self._timeout = timeout_in_sec

    def get_full_path(self, url) -> str:
        if url == '':
            return self._base_url
        return f'{self._base_url}{url if not url.startswith('/') else url[1:]}'

    def __execute(
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
                headers.update(self.headers) if headers is not None and self.headers is not None else self.headers
                with requests.Session() as session:
                    if method.upper() in AllowedMethods:
                        return self._get_response_data(getattr(session, method.lower())(
                            url=self.get_full_path(url),
                            data=data,
                            json=json,
                            params=params,
                            headers=headers
                        ))
                    else:
                        raise RequestMethodNotFoundException(method)
            except requests.exceptions.ConnectionError as e:
                logger.log(f'{self.__class__.__name__} > ConnectionError {e}', 'error')
                if try_wait_if_error:
                    time.sleep(5)
                    continue
                return None
            except requests.exceptions.Timeout as e:
                logger.log(f'{self.__class__.__name__} > Timeout {e}', 'error')
                if try_wait_if_error:
                    time.sleep(20)
                    continue
                return None
            except requests.exceptions.RequestException as e:
                logger.log(f'{self.__class__.__name__} > RequestException {e}', 'error')
                return None
            except AttributeError as e:
                logger.log(f'{self.__class__.__name__} > Attribute {method} -> {e}', 'crit')
                return None

    def _make(
        self,
        url: str,
        method: Method,
        data: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_only_cache: bool = False,
        try_wait_if_error: bool = True,
    ) -> ResponseData | None:
        url = url if not url.startswith('/') else url[1:]

        if self.cache is not None:
            # ! Пытаемся получить кэш по url
            cache_data = self.cache.get(self.get_full_path(url))
            if cache_data is not None:
                # ? Если возвращать только кэш или выполняется условие кэша
                if try_only_cache or self.cache.condition(cache_data):
                    return cache_data

        res = self.__execute(
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
            if self.make_cache:
                self.cache.put(res)

        return res

    @staticmethod
    def _get_response_data(response: requests.Response) -> ResponseData:
        try:
            data = response.json()
            if type(data) is not dict:
                data = {'data': data}
        except (
            requests.exceptions.ContentDecodingError,
            requests.exceptions.JSONDecodeError
        ) as e:
            data = {'error': response.text}
            logger.log(e, 'error')
        return ResponseData(
            url=response.url,
            status=response.status_code,
            headers=response.headers,
            json=data,
        )
