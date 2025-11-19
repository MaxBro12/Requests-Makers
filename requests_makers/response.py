from dataclasses import dataclass
from datetime import datetime
from typing import Literal


Method = Literal['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS']


@dataclass(frozen=True, slots=True)
class ResponseData:
    url: str
    status: int
    headers: dict
    json: dict
    time: datetime = datetime.now()


def time_to_json(time: datetime):
    return time.strftime('%H:%M:%S %d-%m-%Y')


def time_from_json(time):
    return datetime.strptime(time, '%H:%M:%S %d-%m-%Y')
