from os.path import exists
from os import remove
from datetime import timedelta, datetime
from pathlib import Path
from json import load, dump
from abc import ABC, abstractmethod
from .response import ResponseData, time_to_json, time_from_json


class CacheMaker(ABC):
    """
    Класс реализующий методы кэширования.
    Создайте класс с наследующий методы этого класса и реализуйте методы:
    - condition - условие при котором RequestMaker берет кэш а не делает запрос
    - get - забрать данные из кэша
    - put - сохранить кэш
    Пример реализации вы можете посмотреть в реализованном классе BaseCacheMaker.

    Параметры:
    - cache_dir: str - директория где будет расположен кэш
    - allow_headers: tuple | None = None - какие заголовки сохранять, а какие игнорировать. tuple('__all__',) - сохранять все, None - не сохранять
    - ignore_url_part: str = '' - какую часть url нельзя не сохранять в названии файла с кэшем? Например ваш url - http://test_url/test_route и сохраняете этот параметр установлен на "http://test_url/", файл сохранится с названием "test_route.json"
    - encoding: str = 'utf-8' - в каком формате сохранить кэш
    - adt_replace_params: dict | None = None - дополнительный словарь с заменами

    Поле replacer вернет вам словарь как этот класс преобразовывает url в название файла, ключи и значения можно изменить.
    """
    replacer = {
        ' ': '_',
        '/': '_',
        '?': '-',
        '&': '-',
        '%20': '_',
        'http://': '',
        'https://': '',
    }

    def __init__(
        self,
        cache_dir: str = '',
        allow_headers: tuple | None = None,
        ignore_url_part: str | None = None,
        encoding: str = 'utf-8',
        adt_replace_params: dict | None = None
    ):
        self.__cache_dir = cache_dir
        self.__setup_cache_dir(self.__cache_dir)

        self.ignore_url_part = ignore_url_part
        self.allow_headers = allow_headers
        self.encoding = encoding

        if adt_replace_params is not None:
            self.replacer.update(adt_replace_params)

    def __filter_headers(self, headers: dict):
        # Удаление не нужных заголовков
        if self.allow_headers is None:
            return None
        if self.allow_headers[0] == '__all__':
            return headers
        return {k: v for k, v in headers.items() if k in self.allow_headers}

    def __url_to_file(self, url: str) -> str:
        # ! Очистка url и перевод в понятный файл
        if self.ignore_url_part is not None:
            url = url.replace(self.ignore_url_part, '')
        for k, v in self.replacer.items():
            url.replace(k, v)
        return f'{self.__cache_dir}/{url}.json'

    def _get(self, url) -> ResponseData | None:
        f_name = self.__url_to_file(url)
        if exists(f_name):
            with open(f_name, 'r', encoding=self.encoding) as f:
                data = load(f)
                return ResponseData(
                    url=data.get('url', 'url_not_found'),
                    status=data.get('status', 0),
                    headers=data.get('headers'),
                    json=data.get('json'),
                    time=time_from_json(data.get('time', '10:0:0 1-1-2020'))
                )
        return None

    def _put(self, response: ResponseData):
        with open(self.__url_to_file(response.url), 'w', encoding=self.encoding) as f:
            dump({
                "url": response.url,
                "status": response.status,
                "time": time_to_json(response.time),
                "headers": self.__filter_headers(response.headers),
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
    def __init__(
        self,
        cache_dir: str = '',
        allow_headers: tuple | None = None,
        ignore_url_part: str | None = None,
        encoding: str = 'utf-8',
        adt_replace_params: dict | None = None
    ):
        super().__init__(
            cache_dir=cache_dir,
            allow_headers=allow_headers,
            ignore_url_part=ignore_url_part,
            encoding=encoding,
            adt_replace_params=adt_replace_params,
        )

    def condition(self, response_data: ResponseData) -> bool:
        """
        Получает объект ResponseData.
        Ваше условие может быть любым! Важно если этот метод вернет True используем кэш,
        если False - делаем запрос.

        В текущей реализации берет кэш если время запроса было менее 15 минут назад.
        """
        return True if (datetime.now() - response_data.time) <= timedelta(minutes=15) else False

    def get(self, url: str) -> ResponseData | None:
        return self._get(url)

    def put(self, response: ResponseData):
        self._put(response)
