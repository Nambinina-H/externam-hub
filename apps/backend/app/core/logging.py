import logging
import sys
from contextvars import ContextVar

# Identifiant de requête, posé par RequestIDMiddleware et injecté dans chaque log.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """Logs structurés sur stdout, avec le request_id corrélé à chaque ligne."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | req=%(request_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
