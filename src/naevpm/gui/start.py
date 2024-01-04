from importlib import resources
import locale
import logging
from PIL import ImageTk, Image

from naevpm.core.application_logic import ApplicationLogic
from naevpm.core.directories import Directories
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector
from naevpm.gui.gui_controller import GuiController
from naevpm.gui.naevpm_frame import NaevPmFrame
from naevpm.gui.tk_root import TkRoot
from naevpm.gui.tk_threading import TkThreading


def start_gui():
    # Use the system locale
    locale.setlocale(locale.LC_ALL, '')
    logging.basicConfig(level=logging.INFO)
    # TODO logging configuration file
    root = TkRoot(title='Naev Package Manager')

    database_connector = SqliteDatabaseConnector(Directories.DATABASE)

    application_logic = ApplicationLogic(database_connector)
    tk_threading = TkThreading(root)
    gui_controller = GuiController(database_connector, root, tk_threading, application_logic)
    tk_threading.set_update_gui_fn(gui_controller.show_status)

    # Check threads before closing
    def on_delete_window():
        if tk_threading.close():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_delete_window)

    # Using Pillow for more image support in tkinter

    icon_path = resources.files("naevpm.gui.resources").joinpath('icon2.png')
    with resources.as_file(icon_path) as f:
        icon = ImageTk.PhotoImage(Image.open(f))
        root.iconphoto(True, icon)
    naevpm_frame = NaevPmFrame(root, gui_controller)
    naevpm_frame.grid(sticky='NSEW')

    gui_controller.registries_frame = naevpm_frame.registries_frame
    gui_controller.plugins_frame = naevpm_frame.plugins_frame

    gui_controller.refresh_registries_list()
    gui_controller.refresh_plugins_list()

    # Stop dynamic window resizing when contents change in size
    root.update()
    root.geometry(root.geometry())

    root.mainloop()


if __name__ == '__main__':
    start_gui()
