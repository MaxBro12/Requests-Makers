from dataclasses import dataclass
from collections.abc import MutableMapping, Mapping
from datetime import datetime
from typing import Literal

from yarl import URL


Method = Literal['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS']


@dataclass(frozen=True, slots=True)
class ResponseData:
    url: str | URL
    status: int
    headers: dict | MutableMapping | Mapping
    json: dict
    time: datetime = datetime.now()

def time_to_json(time: datetime):
    return time.strftime('%H:%M:%S %d-%m-%Y')

def time_from_json(time):
    return datetime.strptime(time, '%H:%M:%S %d-%m-%Y')

def headers_to_json(headers):
    return dict(headers)
