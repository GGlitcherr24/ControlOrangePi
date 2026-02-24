from loguru import logger
import config

logger.add(
    config.LOG_PATH,
    encoding="utf-8",
    level="DEBUG",
    rotation="1 year"
)

