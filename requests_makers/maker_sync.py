import requests
from .response import ResponseData, Method
from .exceptions import RequestMethodNotFoundException
from .cache import CacheMaker, BaseCacheMaker
from .debug_log import create_log
from .makers_single import Singleton


class HttpMaker(Singleton):
    __session: requests.Session

    def __init__(
        self,
        base_url: str = '',
        headers = None,
        cache_class: CacheMaker = BaseCacheMaker()
    ):
        if headers is None:
            headers = dict()
        self.base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        self.headers = headers
        self.cache = cache_class

        # ! Инициализируем сессию
        self._update_session()

    def __del__(self):
        self.close_session()

    def close_session(self):
        self.__session.close()
        create_log(f'{type(self).__name__} > session closed', 'info')

    def _update_session(self):
        self.__session = requests.Session()
        self.__session.headers = self.headers

    def get_full_path(self, url) -> str:
        return f'{self.base_url}{url}'

    def _make(
            self,
            url: str,
            method: Method,
            data: dict | None = None,
            json: dict | None = None,
            params: dict | None = None,
            headers: dict | None = None,
            try_only_cache: bool = False
    ) -> ResponseData | None:
        url = url if not url.startswith('/') else url[1:]

        try:
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

            # ! Делаем запрос
            match method.upper():
                case 'GET':
                    res = self.__session.get(
                        url=self.get_full_path(url),
                        data=data,
                        json=json,
                        params=params,
                        headers=self.headers.update(headers) if headers is not None else self.headers
                    )
                case 'POST':
                    res = self.__session.post(
                        url=self.get_full_path(url),
                        data=data,
                        json=json,
                        params=params,
                        headers=self.headers.update(headers) if headers is not None else self.headers
                    )
                case 'PUT':
                    res = self.__session.put(
                        url=self.get_full_path(url),
                        data=data,
                        json=json,
                        params=params,
                        headers=self.headers.update(headers) if headers is not None else self.headers
                    )
                case 'DELETE':
                    res = self.__session.delete(
                        url=self.get_full_path(url),
                        data=data,
                        json=json,
                        params=params,
                        headers=self.headers.update(headers) if headers is not None else self.headers
                    )
                case 'HEAD':
                    res = self.__session.head(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'OPTIONS':
                    res = self.__session.options(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )
                case 'PATCH':
                    res = self.__session.patch(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers
                    )

            if res is None:
                raise RequestMethodNotFoundException(method)

            res = self.__get_response_data(res)
            # ! Сохраняем кэш
            if self.make_cache:
                self.cache.put(res)
            return res

        except requests.exceptions.ConnectionError:
            return None

    @staticmethod
    def __get_response_data(response: requests.Response) -> ResponseData:
        try:
            data = response.json()
            if type(data) is not dict:
                data = {'data': data}
        except (
            requests.exceptions.ContentDecodingError,
            requests.exceptions.JSONDecodeError
        ) as e:
            data = {'error': response.text}
        return ResponseData(
            url=response.url,
            status=response.status_code,
            headers=response.headers,
            json=data,
        )
