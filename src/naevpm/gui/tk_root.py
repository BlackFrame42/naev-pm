import logging
from tkinter import Tk, FALSE

from naevpm.gui.error_window import ErrorWindow

logger = logging.getLogger(__name__)


class TkRoot(Tk):
    windowing_system: str

    def on_delete_window_event(self):
        self.destroy()

    # noinspection PyPep8Naming
    def __init__(self, title: str, screenName=None, baseName=None, useTk=True, sync=False, use=None):
        # Gnome uses class name as the text that appears in the window switcher
        className = title
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title(title)

        self.option_add('*tearOff', FALSE)  # See https://tkdocs.com/tutorial/menus.html section "Before you Start"
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Check windowing system
        self.windowing_system = self.tk.call('tk', 'windowingsystem')  # returns x11, win32 or aqua
        logger.info(f"tkinter windowing system '{self.windowing_system}'")

        logger.info("tkinter root initialized")

    # Override default exception handler
    def report_callback_exception(self, exc, val, tb):
        logging.error("Unhandled error occurred", exc_info=(exc, val, tb))
        error_window = ErrorWindow(self)
        error_window.set_error(exc, val, tb)
