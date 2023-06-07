"""Модуль содержит исключений для key-value-хранилищ."""


class MissKeyValueInterfaceRealisation(Exception):
    """Исключение выбрасывается в том случае, если для заданного клиента нет реализации интерфейса."""

    def __init__(self, client, message='Для заданного клиента нет реализованного интерфейса хранилища.'):
        self.client_type = type(client)
        self.message = message
        super().__init__(self.message)
