import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "app.log"

MAX_BYTES = 100 * 1024 * 1024  # 100MB
RETENTION_DAYS = 3
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60


class RetentionRotatingFileHandler(RotatingFileHandler):
    """Size-based rotating file handler with age-based cleanup."""

    def _cleanup_expired_logs(self) -> None:
        now = time.time()
        # Rotated files look like app.log.1, app.log.2, ...
        for file_path in LOG_DIR.glob(f"{LOG_FILE.name}*"):
            if file_path.is_dir():
                continue
            if now - file_path.stat().st_mtime > RETENTION_SECONDS:
                file_path.unlink(missing_ok=True)

    def doRollover(self) -> None:
        super().doRollover()
        self._cleanup_expired_logs()


def _build_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("car_sales_agent")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    file_handler = RetentionRotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=9999,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False

    file_handler._cleanup_expired_logs()
    return logger


logger = _build_logger()


__all__ = ["logger"]
