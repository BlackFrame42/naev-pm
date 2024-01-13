from tkinter import ttk

from naevpm.core.config import Config
from naevpm.core.models import registry_fields, RegistryDbModel
from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.add_registry_window import AddRegistryWindow
from naevpm.gui.data_model_to_str_list import registry_to_str_list
from naevpm.gui.display_utils import field_name_as_list_header
from naevpm.gui.synced_tree_view import SyncedTreeView

from naevpm.gui.tk_root import TkRoot
from naevpm.gui.treeview_context_menu import TreeviewContextMenu


class RegistriesFrame(ttk.Frame):
    _registries_list: SyncedTreeView
    add_registry_window: AddRegistryWindow

    def __init__(self, parent: ttk.Widget, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(parent, **kwargs)

        # The additional window to add registries will already be prepared and exists only once.
        self.add_registry_window = AddRegistryWindow(root, gui_controller)
        # Hide it for now (not visible in the task bar of the windowing system)
        self.add_registry_window.withdraw()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Buttons on top of the list -----------------------------------------
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(column=0, row=0, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        buttons_frame.columnconfigure(0, weight=1)

        add_button = ttk.Button(buttons_frame, text="Add registry", command=self.add_registry_window.show)
        add_button.grid(column=0, row=0, sticky='E', **Config.GLOBAL_GRID_PADDING)

        def import_installed_plugins():
            gui_controller.import_existing_plugins_to_index()

        import_button = ttk.Button(buttons_frame, text="Import installed plugins", command=import_installed_plugins)
        import_button.grid(column=1, row=0, sticky='E', **Config.GLOBAL_GRID_PADDING)

        def fetch_plugin_metadata_from_all_registries():
            for registry in self._registries_list.get_all_objects():
                gui_controller.fetch_registry_plugin_metadatas(registry)

        fetch_all_button = ttk.Button(buttons_frame, text="Fetch plugin metadata from all registries",
                                      command=fetch_plugin_metadata_from_all_registries)
        fetch_all_button.grid(column=2, row=0, sticky='E', **Config.GLOBAL_GRID_PADDING)

        # Registry list -----------------------------------------
        list_frame = ttk.Frame(self)
        list_frame.grid(column=0, row=1, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        def get_object_identifier(r: RegistryDbModel):
            return r.source

        self._registries_list = SyncedTreeView(
            get_str_values_fn=registry_to_str_list,
            get_object_identifier_fn=get_object_identifier,
            master=list_frame,
            columns=registry_fields,
            show='headings',
            selectmode='browse')
        list_scrollbar = ttk.Scrollbar(list_frame,
                                       orient="vertical",
                                       command=self._registries_list.yview)
        self._registries_list.configure(yscrollcommand=list_scrollbar.set)
        list_scrollbar.grid(column=1, row=0, sticky='NSE')
        for registry_field in registry_fields:
            self._registries_list.heading(registry_field, text=field_name_as_list_header(registry_field))
        self._registries_list.grid(column=0, row=0, sticky='NSEW')
        list_item_context_menu = TreeviewContextMenu(self._registries_list, root, lambda iid: None)

        def remove_registry():
            registry = self._registries_list.get_object_by_iid(list_item_context_menu.item_id)
            gui_controller.remove_registry(registry)
            self._registries_list.focus_set()

        list_item_context_menu.add_command(
            label='Remove registry',
            command=remove_registry)

        def fetch_plugin_metadata_from_registry():
            registry = self._registries_list.get_object_by_iid(list_item_context_menu.item_id)
            gui_controller.fetch_registry_plugin_metadatas(registry)
            # self.focus_set()

        list_item_context_menu.add_command(
            label='Fetch registry index',
            command=fetch_plugin_metadata_from_registry)

    # Functions for use by GUI controller -----------------------------------------
    def put_registry(self, registry: RegistryDbModel):
        self._registries_list.sync_put(registry)

    def put_registries(self, registries: list[RegistryDbModel]):
        self._registries_list.sync_put_all(registries)

    def clear_registries(self):
        self._registries_list.sync_clear()

    def update_registry(self, registry: RegistryDbModel):
        self._registries_list.sync_update(registry)

    def remove_registry(self, registry: RegistryDbModel):
        self._registries_list.sync_remove(registry)
