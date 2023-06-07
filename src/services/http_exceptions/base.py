"""Модуль, описывающий базовое http-исключение"""
from dataclasses import dataclass
from http import HTTPStatus

from schemes import base_schema, BaseResponseSchema


@dataclass
class Error:
    msg: str
    detail: str


class HTTPException(Exception):
    def __init__(self, msg: str, http_status: HTTPStatus, detail_msg: str | None = ''):
        """
        Инициализирующий метод.

        Args:
            msg: сообщение ошибки
            http_status: http код ошибки
            detail_msg: детальная информация об ошибке.
        """
        self.error = Error(msg, detail_msg)
        self.http_status = http_status
        super().__init__(self.error.msg)

    def response(self) -> tuple[BaseResponseSchema, HTTPStatus]:
        return base_schema.dump(dict(
            msg=self.error.msg,
            details=self.error.detail,
        )), self.http_status
