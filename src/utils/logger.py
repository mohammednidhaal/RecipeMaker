import logging
import sys

logger = logging.getLogger("RecipeMate")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [RecipeMate] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_step(phase: str, message: str, **kwargs):
    extra = f" | {kwargs}" if kwargs else ""
    logger.info(f"[{phase.upper()}] {message}{extra}")
