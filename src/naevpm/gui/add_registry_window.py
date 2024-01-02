from tkinter import Toplevel, ttk, StringVar

from naevpm.core.config import Config
from naevpm.gui.abstract_gui_controller import AbstractGuiController

from naevpm.gui.tk_root import TkRoot


class AddRegistryWindow(Toplevel):
    _source_entry: ttk.Entry

    def __init__(self, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        title = 'Add Repository'
        # class_ needs to be set to the title to show the right text in the window switcher
        super().__init__(root, class_=title, **kwargs)
        self.title(title)

        # Just hide the window instead of destroying it when closing it.
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self)
        frame.grid(sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        # Entry ---------------------------------
        source_label = ttk.Label(frame, text='Source')
        source_label.grid(column=0, row=1, **Config.GLOBAL_GRID_PADDING)
        source_text = StringVar()
        self._source_entry = ttk.Entry(frame, textvariable=source_text)

        self._source_entry.grid(column=1, row=1, **Config.GLOBAL_GRID_PADDING)

        # Buttons -----------------------------------------
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(column=0, columnspan=2, row=3, sticky='WES', **Config.GLOBAL_GRID_PADDING)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)

        cancel_button = ttk.Button(buttons_frame, text='Cancel', command=self.withdraw)
        cancel_button.grid(column=0, row=0, sticky='W', **Config.GLOBAL_GRID_PADDING)

        def add_registry():
            source = source_text.get().strip()
            gui_controller.add_registry(source)

        add_button = ttk.Button(buttons_frame, text='Add', command=add_registry, default='active')
        self._source_entry.bind('<Return>', lambda ev: add_registry())
        add_button.grid(column=1, row=0, sticky='E')

    def show(self):
        # Add window to the taskbar and screen
        self.deiconify()
        # Set focus on text entry
        self._source_entry.focus_set()
        # Make sure it is on the top
        self.lift()
