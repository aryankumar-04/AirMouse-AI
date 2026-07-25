"""
AirMouse AI - Production Logging Architecture.

Provides centralized logger setup supporting Development and Production modes,
third-party C++ output suppression, RotatingFileHandler, path sanitization,
and thread-safe GUI log queue handling.
"""

import contextlib
import logging
import logging.handlers
import os
import queue
import re
import sys
from typing import Optional

# 1. Environment Variable Setup for Third-Party C++ Logging Suppression
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"
os.environ["ABSL_LOGGING_MIN_LOG_LEVEL"] = "3"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

# Suppress Python level third-party logger noise
for lib_logger in ["absl", "mediapipe", "tensorflow", "urllib3", "PIL"]:
    logging.getLogger(lib_logger).setLevel(logging.ERROR)

# Global thread-safe queue for GUI log viewer
gui_log_queue: queue.Queue = queue.Queue(maxsize=1000)


@contextlib.contextmanager
def suppress_c_stderr(enabled: bool = True):
    """
    Context manager to temporarily redirect low-level C/C++ stderr (FD 2)
    to os.devnull. Used during C++ library initialization (e.g. MediaPipe / TFLite)
    in Production Mode to swallow native delegate spam.
    """
    if not enabled:
        yield
        return

    try:
        stderr_fd = sys.stderr.fileno()
    except (AttributeError, ValueError, Exception):
        yield
        return

    with open(os.devnull, "w") as devnull:
        old_stderr_fd = None
        try:
            old_stderr_fd = os.dup(stderr_fd)
            os.dup2(devnull.fileno(), stderr_fd)
            yield
        finally:
            if old_stderr_fd is not None:
                os.dup2(old_stderr_fd, stderr_fd)
                os.close(old_stderr_fd)


def sanitize_message(msg: str) -> str:
    """Strips absolute machine directories, usernames, and machine paths from log messages for security."""
    if not isinstance(msg, str):
        return str(msg)

    # Replace absolute project & user paths with clean relative notation
    msg = re.sub(r"[A-Za-z]:\\[^:\n]+\\AirMouse AI\\?", "", msg)
    msg = re.sub(r"[A-Za-z]:/?[^/\n]+/AirMouse AI/?", "", msg)
    msg = re.sub(r"C:\\Users\\[^\s\\]+\\", "~/", msg)
    msg = re.sub(r"/Users/[^/\s]+/", "~/", msg)
    return msg


class ProductionFormatter(logging.Formatter):
    """Clean, production-safe formatter that sanitizes machine paths."""

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = sanitize_message(record.msg)
        formatted = super().format(record)
        record.msg = original_msg
        return formatted


class GUILogHandler(logging.Handler):
    """Custom logging handler emitting formatted log records to a thread-safe Queue."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        """Pushes formatted log record into the queue."""
        try:
            msg = self.format(record)
            if self.log_queue.full():
                try:
                    self.log_queue.get_nowait()
                except queue.Empty:
                    pass
            self.log_queue.put_nowait((record.levelname, msg))
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str = "AirMouseAI",
    log_mode: str = "RELEASE",
    log_level: Optional[str] = None,
    log_file: Optional[str] = "logs/airmouse.log",
    debug_mode: bool = False,
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_file_size_mb: int = 5,
    backup_count: int = 5
) -> logging.Logger:
    """
    Configures and returns a thread-safe production-grade Logger supporting three modes:
      1. RELEASE (Production Default): Console stays 100% clean (CRITICAL only). Logs info to file.
      2. INFO: Console & File show high-level lifecycle events.
      3. DEBUG: Console & File show detailed developer metrics & tracebacks.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    # Resolve mode and level mapping
    effective_mode = log_mode.upper() if log_mode else "RELEASE"
    if debug_mode or log_level == "DEBUG":
        effective_mode = "DEBUG"
    elif log_level == "INFO" and effective_mode == "RELEASE":
        effective_mode = "INFO"

    if effective_mode == "DEBUG":
        file_level = logging.DEBUG
        console_level = logging.DEBUG
    elif effective_mode == "INFO":
        file_level = logging.INFO
        console_level = logging.INFO
    else:  # RELEASE Mode (Default Production Mode)
        file_level = logging.INFO
        console_level = logging.CRITICAL  # Completely silent console during normal operation

    logger.setLevel(logging.DEBUG)

    # Standard clean production log format
    formatter = ProductionFormatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (Silent in RELEASE mode unless CRITICAL error occurs)
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 2. Rotating File Handler (Captures diagnostics up to file_level without path exposure)
    if log_to_file and log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            max_bytes = max_file_size_mb * 1024 * 1024
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as err:
            sys.stderr.write(f"Could not initialize file logger '{log_file}': {err}\n")

    # 3. GUI Queue Handler
    gui_handler = GUILogHandler(gui_log_queue)
    gui_handler.setLevel(file_level)
    gui_handler.setFormatter(formatter)
    logger.addHandler(gui_handler)

    return logger
