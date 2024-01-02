from tkinter import ttk, StringVar

from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.plugins_frame import PluginsFrame
from naevpm.gui.registries_frame import RegistriesFrame
from naevpm.gui.tk_root import TkRoot


class NaevPmFrame(ttk.Frame):
    status_text: StringVar
    registries_frame: RegistriesFrame
    plugins_frame: PluginsFrame

    def background_task_update_fn(self, msg: str):
        self.status_text.set(msg)

    def __init__(self, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(root, **kwargs)

        notebook = ttk.Notebook(self)
        self.registries_frame = RegistriesFrame(notebook, root, gui_controller)
        self.plugins_frame = PluginsFrame(notebook, root, gui_controller)
        notebook.add(self.registries_frame, text='Registries')
        notebook.add(self.plugins_frame, text='Plugins')
        notebook.grid(column=0, row=0, sticky='NSEW')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.status_text = StringVar(value='')
        status_bar = ttk.Label(self, textvariable=self.status_text)
        status_bar.grid(column=0, row=1, sticky='SEW')
        # self.rowconfigure(1, weight=0)

        gui_controller.status_text = self.status_text
