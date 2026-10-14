"""Full tracebacks go to the log file (and stdout, for `fly logs`); the client only ever gets a generic
message -- see app.py's exception handler. This replaces live_demo/server.py's `{"error": str(e)}` pattern,
which is fine for a local single-user demo and not acceptable once a real technician is unsupervised."""
import logging
import logging.handlers

from . import config


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("pilot")
    if logger.handlers:            # idempotent -- uvicorn's reloader can import this module twice
        return logger
    logger.setLevel(logging.INFO)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(config.LOG_PATH, maxBytes=5_000_000, backupCount=5)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    return logger


log = setup_logging()
