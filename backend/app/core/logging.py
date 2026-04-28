from __future__ import annotations

import json
import logging
import logging.config
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

from app.core.config import Settings

REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": REQUEST_ID_CTX.get(),
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_payload"):
            payload["extra"] = record.extra_payload
        return json.dumps(payload, ensure_ascii=True)


def set_request_id(request_id: str) -> None:
    REQUEST_ID_CTX.set(request_id)


def get_request_id() -> str:
    return REQUEST_ID_CTX.get()


def configure_logging(settings: Settings) -> None:
    formatter = JsonFormatter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_file_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.log_level.upper())
    root.addHandler(console)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

