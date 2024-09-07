#!/usr/bin/env python3

import inspect

import logging
from logging import FileHandler, StreamHandler, Formatter


class PyFyzzLogger:
    def __init__(
        self,
        name: str = "pyfyzzlogger",
        log_file: str = "pyfyzz.log",
        level: str = "info",
    ):
        self.logger = logging.getLogger(name)
        self.level = level

        # Set the logging level based on the provided level string
        if self.level == "error":
            self.logger.setLevel(logging.ERROR)  # Set level to ERROR
        elif self.level == "debug":
            self.logger.setLevel(logging.DEBUG)  # Set level to DEBUG
        else:
            self.logger.setLevel(logging.INFO)  # Default to INFO

        # Avoid adding multiple handlers
        if not self.logger.hasHandlers():
            # File handler for logging to a file
            file_handler = FileHandler(log_file)

            # Console handler for logging to the console
            console_handler = StreamHandler()

            # Create a custom formatter
            formatter = Formatter(
                "%(asctime)s - %(levelname)s - %(class_method)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Assign formatter to handlers
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers to the logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def _get_class_method_info(self):
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)

        # Find the frame where the function is called
        for f in outer_frames:
            if f.function not in ["_get_class_method_info", "__init__", "log"]:
                break

        # Extract class and method info
        cls = f.frame.f_locals.get("self", None)
        cls_name = cls.__class__.__name__ if cls else None
        method_name = f.function

        return f"{cls_name}.{method_name}" if cls_name else method_name

    def log(self, level, msg, *args, **kwargs):
        class_method_info = self._get_class_method_info()

        # Add class_method info to extra dict for formatter to use
        extra = {"class_method": class_method_info}

        if level == "debug":
            self.logger.debug(msg, *args, extra=extra, **kwargs)
        elif level == "info":
            self.logger.info(msg, *args, extra=extra, **kwargs)
        elif level == "warning":
            self.logger.warning(msg, *args, extra=extra, **kwargs)
        elif level == "error":
            self.logger.error(msg, *args, extra=extra, **kwargs)
        else:
            self.logger.log(level, msg, *args, extra=extra, **kwargs)
