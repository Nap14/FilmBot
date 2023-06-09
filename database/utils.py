import datetime
from typing import Callable

import colorama
import winsound


class AsDecoratorMixin:
    """
    This code defines a mixin class that can be used to create a decorator that applies a context manager to a function.
    """

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper


class ExceptionHandler(AsDecoratorMixin):
    """
    The ExceptionHandler class is a Python class that can be used as a context manager to handle exceptions in a specific way.
    It has two methods, __enter__ and __exit__, which are called when the context is entered and exited, respectively
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception occurred, beep at 2500Hz for 1 second
        if exc_type is not None:
            winsound.Beep(2500, 1000)
            return

        # Otherwise, play the default beep sound
        winsound.MessageBeep(winsound.MB_OK)
        print(
            colorama.Fore.GREEN
            + "All tasks are completed successfully🎉"
            + colorama.Style.RESET_ALL
        )


class Timer(AsDecoratorMixin):
    """
    A context manager for timing the execution of a block of code.

    Usage:
    ------
    with Timer():
        # Code to be timed here
    """

    def __enter__(self):
        self.start_time = datetime.datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context and calculates the elapsed time. Prints the result
        to the console in green if the process completed successfully, and
        in red if an exception was raised.
        """
        elapsed = self._elapsed_time()

        if exc_type is not None:
            print(
                colorama.Fore.RED
                + f"Process exited with an exception: {exc_val} for {elapsed}"
            )
            return

        print(
            colorama.Fore.GREEN
            + f"Process finished for {elapsed}"
            + colorama.Style.RESET_ALL
        )

    def _elapsed_time(self):
        return datetime.datetime.now() - self.start_time


def print_info(message: str, method: Callable = len, color: colorama = "CYAN"):
    """
    Decorator function that prints information about the result of a function call.

    Arguments:
    - message (str): the message that will be printed along with the result of the function call

    Optional arguments:
    - method (Callable): a callable object that will be used to process the result of the function call
      (default: len, which returns the length of the object)
    - color (colorama): the color that will be used to print the message (default: CYAN)
    """

    try:
        color = getattr(colorama.Fore, color.upper())
    except AttributeError:
        raise ValueError(f"Invalid color name: {color}")

    if not callable(method):
        raise ValueError("Method argument must be callable.")

    def decorator(func: callable):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            print(color + f"{method(result)} {message}" + colorama.Style.RESET_ALL)
            return result

        return wrapper

    return decorator
