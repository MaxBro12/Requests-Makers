from datetime import timedelta, datetime
from pathlib import Path
from json import load, dump
from os.path import exists
from os import remove
from abc import ABC, abstractmethod
from .requests_dataclasses import ResponseData, headers_to_json, time_to_json, time_from_json


class CacheMaker(ABC):
    """
    Класс реализующий методы кэширования. Не пытайтесь использовать его в отрыве от BaseCacheMaker!
    HttpMaker не может работать без методов реализованных в BaseCacheMaker!!!
    Параметры:
    - cache_dir: str - директория где будет расположен кэш
    - ignore_headers: bool - сохранять ли response.headers
    - allow_headers: tuple - (работает только если ignore_headers = True) какие заголовки сохранять, а какие игнорировать. __all__ - сохранять все
    """
    def __init__(
        self,
        cache_dir: str = '',
        ignore_headers: bool = False,
        allow_headers: tuple = ('__all__',),
        ignore_url_part: str | None = None
    ):
        self.__cache_dir = cache_dir
        self.__setup_cache_dir(self.__cache_dir)

        self.ignore_url_part = ignore_url_part
        self.ignore_headers: bool = ignore_headers
        self.allow_headers: tuple = allow_headers

    def __filter_headers(self, headers: dict):
        if self.allow_headers[0] == '__all__':
            return headers
        return {k: v for k, v in headers.items() if k in self.allow_headers}

    def __url_to_file(self, url: str) -> str:
        # ! Очистка url и перевод в понятный файл
        if self.ignore_url_part is not None:
            url = url.replace(self.ignore_url_part, '0')
        url = url.removesuffix('/').replace('/', '_').replace('=', '-')\
            .replace('?', '').replace('&', '.').replace('%20', '_')\
            .replace(' ', '_')\
            .replace('https:', '_').replace('http:', '_') # ! Обазятельно игнорить!
        return f'{self.__cache_dir}/.cache_{url}.json'

    def _get(self, url) -> ResponseData | None:
        f_name = self.__url_to_file(url)
        if exists(f_name):
            with open(f_name, 'r', encoding='utf8') as f:
                data = load(f)
                return ResponseData(
                    url=data['url'],
                    status=data['status'],
                    headers=data['headers'],
                    json=data['json'],
                    time=time_from_json(data['time'])
                )
        return None

    def _put(self, response: ResponseData):
        with open(self.__url_to_file(response.url), 'w', encoding='utf8') as f:
            dump({
                "url": response.url,
                "status": response.status,
                "time": time_to_json(response.time),
                "headers": self.__filter_headers(headers_to_json(response.headers)) if self.ignore_headers is not True else None,
                "json": response.json
            }, f)

    def rm_cache(self, url) -> bool:
        f_name = self.__url_to_file(url)
        if exists(f_name):
            remove(f_name)
            return True
        return False

    def __setup_cache_dir(self, cache_dir: str):
        self.__cache_dir = cache_dir.removesuffix('/')
        Path(self.__cache_dir).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get(self, url: str) -> ResponseData | None:
        pass

    @abstractmethod
    def put(self, response: ResponseData):
        pass

    @abstractmethod
    def condition(self, response_data: ResponseData) -> bool:
        pass


class BaseCacheMaker(CacheMaker):
    """
    BaseCacheMaker - базовый класс работы с кэшем.
    Вы можете так же создать свой класс. Но тот ОБЯЗАН реализовывать методы:

    get - забрать данные из кэша. Возвращается объект ResponseData если условие выполнено верно если нет None
    put - сохранить кэш
    condition - условие при котором берется именно кэш, а не делается запрос! Возвращает bool
    """
    def __init__(self, cache_dir: str = ''):
        super().__init__(
            cache_dir=cache_dir
        )

    def condition(self, response_data: ResponseData) -> bool:
        """
        Получает объект ResponseData.
        Ваше условие может быть любым! Важно то что если этот метод вернет True мы используем кэш,
        если False мы делаем запрос
        """
        return True if (datetime.now() - response_data.time) <= timedelta(minutes=15) else False

    def get(self, url: str) -> ResponseData | None:
        return self._get(url)

    def put(self, response: ResponseData):
        self._put(response)
