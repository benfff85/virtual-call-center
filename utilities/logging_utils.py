import logging
import sys


def configure_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger that outputs to the console with a specified format.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Create a logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Define a log format that includes date, time, log level, and message
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    console_handler.setFormatter(formatter)

    # Add the console handler to the logger
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger