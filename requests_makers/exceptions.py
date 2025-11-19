import logging


class RequestMethodNotFoundException(Exception):
    def __init__(self, method: str):
        txt = f'Request method not found: {method}'
        logging.error(txt, 'error')
        super().__init__(txt)
