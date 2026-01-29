import logging
import os
import platform
import sys
import time
from typing import Final, Literal

from colorama import Fore, Style

PROFILE: Final[Literal[19]] = 19


class CustomFormatter(logging.Formatter):
    def __init__(
        self,
        datefmt: str | None = None,
        verbose: bool = False,
    ):
        self.verbose = verbose

        # Setup the format info based on verbosity
        if self.verbose:
            # the syntax "-8" add space char to levelname if levelname length is less than 7
            self.format_info = "[%(name)s - %(levelname)-8s%(asctime)s (P:%(process)d - T:%(thread)d)]: "
        else:
            self.format_info = (
                "[%(levelname)-8s%(asctime)s | %(filename)s:%(lineno)d]: "
            )

        self.format_message = "%(message)s"
        fmt = self.format_info + self.format_message

        # Call the base class constructor with the format and date format
        # NOTE: use the default format style "%" of the constructor
        super().__init__(fmt=fmt, datefmt=datefmt)


class CustomColoredFormatter(CustomFormatter):
    # NOTE: the console formatter subclasses the file formatter and add colored logs
    def __init__(self, datefmt: str | None = None, verbose: bool = False):
        # NOTE: colored console output support on Windows
        if platform.system() == "Windows":
            # https://github.com/tartley/colorama
            # On Windows, enable ANSI color codes
            from colorama import just_fix_windows_console

            just_fix_windows_console()

        # Call the base class constructor with the format and date format
        # NOTE: use the default format style "%" of the constructor
        super().__init__(datefmt=datefmt, verbose=verbose)

    def _make_message(self, ansi_code: str) -> str:
        """Takes the log string and formats it with color

        Args:
            ansi_code (str): ANSI foreground colored code

        Returns:
            str: the formatted colored text
        """
        return ansi_code + self.format_info + Style.RESET_ALL + self.format_message

    # mappings between log levels and ANSI colored codes
    FORMATS = {
        logging.DEBUG: Fore.CYAN,
        PROFILE: Fore.GREEN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.FORMATS.get(record.levelno, Style.RESET_ALL)
        log_fmt = self._make_message(color)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)


def optimizeLogging(verbose: bool = False) -> None:
    if not verbose:
        logging._srcfile = None
        logging.logThreads = False
        logging.logProcesses = False
        logging.logMultiprocessing = False


def setConsoleHandler(
    logger: logging.Logger, datefmt: str | None = None, verbose: bool = False
):
    # Set the console handler with the custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = CustomColoredFormatter(datefmt, verbose)
    console_handler.setFormatter(console_formatter)
    # console_handler.setLevel(logger.getEffectiveLevel())
    logger.addHandler(console_handler)


def setFileHandler(
    logger: logging.Logger, path: str, datefmt: str | None = None, verbose: bool = False
):
    os.makedirs(path, exist_ok=True)
    log_file = os.path.join(path, "app.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(CustomFormatter(datefmt, verbose))
    logger.addHandler(file_handler)


def get_logger(
    logger_name: str,
    level: str | int = "INFO",
    path_to_save: str | None = None,
    verbose: bool = False,
) -> logging.Logger:
    """
    Args:
        logger_name: Name of the logger used to display/save logger records
        level: Logging of the level messages displayed
        path_to_save: Path where the log file is saved

    Returns:
        Logger to use in modules
    """
    logger_name = logger_name.replace(".", "/") + ".py"
    logging.addLevelName(PROFILE, "PROFILE")
    logger = logging.getLogger(name=logger_name)
    # Convert the string to the corresponding logging level constant
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)

    # Prevent adding multiple handlers to the logger
    if not logger.hasHandlers():
        datefmt = "%Y-%m-%d %H:%M:%S"

        # Logging to console
        setConsoleHandler(logger, datefmt, verbose)

        # Logging to file
        if path_to_save:
            setFileHandler(logger, path_to_save, datefmt, verbose)

    # up-stream BUG FIXES:
    # See: https://github.com/aws-samples/amazon-textract-textractor/issues/367
    logger.propagate = False

    return logger


def timer(func, logger_name: str = "profiler", logger_level: int = PROFILE):
    logger = get_logger(logger_name, logger_level)

    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 60:
                minutes, seconds = divmod(elapsed_time, 60)
                logger.log(
                    level=PROFILE,
                    msg=f"Function {func.__name__} took {int(minutes)}m{int(seconds)}s to execute.",
                )
            else:
                logger.log(
                    level=PROFILE,
                    msg=f"Function {func.__name__} took {elapsed_time:.3f} seconds to execute.",
                )
        return result

    return wrapper


def async_timer(func, logger_name: str = "profiler", logger_level: int = PROFILE):
    logger = get_logger(logger_name, logger_level)

    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
        finally:
            elapsed_time = time.perf_counter() - start_time
            # extra = {"name": "PROFILE"}
            if elapsed_time > 60:
                minutes, seconds = divmod(elapsed_time, 60)
                logger.log(
                    level=PROFILE,
                    msg=f"Function {func.__name__} took {int(minutes)}m{int(seconds)}s to execute.",
                )
            else:
                logger.log(
                    level=PROFILE,
                    msg=f"Function {func.__name__} took {elapsed_time:.3f} seconds to execute.",
                )
        return result

    return wrapper


if __name__ == "__main__":
    logger = get_logger(__name__, level="DEBUG", path_to_save="logs", verbose=False)
    logger.info("Test log")
    logger.debug("A debug message")
    logger.error("An error message")

    import asyncio

    @async_timer
    async def prova():
        await asyncio.sleep(1)
        logger.info("prova")

    asyncio.run(prova())
