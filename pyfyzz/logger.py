import logging
import inspect
from logging import FileHandler, StreamHandler, Formatter


class PyFyzzLogger:
    def __init__(
        self,
        name: str = "pyfyzzlogger",
        log_file: str = "pyfyzz.log",
        level=logging.DEBUG,
    ):
        self.logger = logging.getLogger(name)
        self.level = level
        self.logger.setLevel(self.level)

        # Avoid adding multiple handlers
        if not self.logger.hasHandlers():
            # File handler for logging to a file
            file_handler = FileHandler(log_file)
            file_handler.setLevel(level)

            # Console handler for logging to the console
            console_handler = StreamHandler()
            console_handler.setLevel(level)

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
