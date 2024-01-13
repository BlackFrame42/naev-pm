from tkinter import ttk, VERTICAL

from naevpm.core.config import Config
from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.plugins_frame import PluginsFrame
from naevpm.gui.registries_frame import RegistriesFrame
from naevpm.gui.tk_root import TkRoot


class NaevPmFrame(ttk.Frame):
    registries_frame: RegistriesFrame
    plugins_frame: PluginsFrame
    _log_line_count: int

    def __init__(self, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(root, **kwargs)

        self._log_line_count = 0

        p = ttk.Panedwindow(self, orient=VERTICAL)
        p.grid(column=0, row=0, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        # p.columnconfigure(0, weight=1)
        # p.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(p)
        self.registries_frame = RegistriesFrame(notebook, root, gui_controller)
        self.plugins_frame = PluginsFrame(notebook, root, gui_controller)
        notebook.add(self.registries_frame, text='Registries', underline=0)
        notebook.add(self.plugins_frame, text='Plugins', underline=0)
        notebook.grid(column=0, row=0, sticky='NSEW')
        notebook.columnconfigure(0, weight=1)
        notebook.rowconfigure(0, weight=1)

        root.bind('<Key-r>', lambda ev: notebook.select(0))
        root.bind('<Key-R>', lambda ev: notebook.select(0))
        root.bind('<Key-p>', lambda ev: notebook.select(1))
        root.bind('<Key-P>', lambda ev: notebook.select(1))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(p)
        list_frame.grid(column=0, row=1, sticky='SEW', **Config.GLOBAL_GRID_PADDING)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        p.add(notebook, weight=1)
        p.add(list_frame)

        self.log = ttk.Treeview(list_frame, height=3, show=[], columns=['log'])
        self.log.grid(column=0, row=0, sticky='NSEW')
        log_scrollbar = ttk.Scrollbar(list_frame,
                                      orient="vertical",
                                      command=self.log.yview)
        self.log.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.grid(column=1, row=0, sticky='NSE')

    def add_log_line(self, log_line: str):
        self._log_line_count += 1
        if self._log_line_count > 200:
            self.log.delete(self.log.get_children()[0])
            self._log_line_count -= 1
        self.log.insert('', 'end', values=[log_line])
        self.log.yview_moveto(1)
