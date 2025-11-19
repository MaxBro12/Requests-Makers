from .debug_log import create_log


class RequestMethodNotFoundException(Exception):
    def __init__(self, method: str):
        txt = f'Request method not found: {method}'
        create_log(txt, 'error')
        super().__init__(txt)
