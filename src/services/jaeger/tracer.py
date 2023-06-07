"""Модуль настроек трассировки."""
from flask import request
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import (Resource, SERVICE_NAME, TELEMETRY_SDK_VERSION, TELEMETRY_SDK_LANGUAGE,
                                         TELEMETRY_SDK_NAME)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from core.config import DB_SETTINGS
from services.utils import coroutine


def configure_tracer() -> None:
    """Метод конфигурирует сэмплер."""
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource(
                {
                    TELEMETRY_SDK_LANGUAGE: DB_SETTINGS.jaeger_telemetry_sdk_language,
                    TELEMETRY_SDK_NAME: DB_SETTINGS.jaeger_telemetry_sdk_name,
                    TELEMETRY_SDK_VERSION: DB_SETTINGS.jaeger_telemetry_sdk_version,
                    SERVICE_NAME: DB_SETTINGS.jaeger_service_name
                }
            )
        )
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=DB_SETTINGS.jaeger_host,
                agent_port=DB_SETTINGS.jaeger_port,
            )
        )
    )
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


@coroutine
def set_trace_by_span_name(span_name: str):
    """Метод создаёт дочерние спаны"""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(span_name):
        yield


def setup_tracer():
    """Метод проверяет наличие заголовка `X-Request-Id` и устанавливает спану тэг."""

    request_id = request.headers.get('X-Request-Id')
    if not request_id:
        raise RuntimeError('request id is required')
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span('auth')
    span.set_attribute('http.request_id', request_id)
    span.end()
