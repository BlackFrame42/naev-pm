import tkinter
import traceback
from tkinter import Toplevel, Tk, ttk, StringVar
from tkinter.scrolledtext import ScrolledText


class ErrorWindow(Toplevel):
    error_text_field: ScrolledText

    def ok(self):
        self.withdraw()

    def set_error(self, exc, val, tb):
        message = f"""
An unexpected error occurred which was not properly handled by the application. 
Please send a description of your last actions, this error description and the application's logs to the developers.

Type: {exc.__name__} \n
Error: {str(val)}

{''.join(traceback.format_tb(tb))}
"""
        self.error_text_field.insert(tkinter.INSERT, message)
        self.error_text_field.configure(state='disabled')

    def __init__(self, parent: Tk, **kwargs):
        super().__init__(parent, **kwargs)
        self.error_text = StringVar()
        self.title('Unhandled error occurred')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self)
        frame.grid(sticky="NSEW")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.error_text_field = ScrolledText(frame)
        self.error_text_field.grid(column=0, row=0, sticky="NSEW")

        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(column=0, row=1, sticky="WES")
        buttons_frame.rowconfigure(0, weight=1)
        buttons_frame.columnconfigure(0, weight=1)

        ok_button = ttk.Button(buttons_frame, text='Close', command=self.ok)
        ok_button.grid(column=0, row=0)
