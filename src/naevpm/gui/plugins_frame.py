from tkinter import ttk, E, DISABLED, NORMAL, StringVar, Event, font

from naevpm.core.config import Config
from naevpm.core.models import plugin_fields, PluginDbModel, PluginState
from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.data_model_to_str_list import plugin_to_str_list
from naevpm.gui.display_utils import field_name_as_list_header, display_boolean
from naevpm.gui.synced_tree_view import SyncedTreeView
from naevpm.gui.tk_root import TkRoot
from naevpm.gui.treeview_context_menu import TreeviewContextMenu


class PluginsFrame(ttk.Frame):
    _plugins_list: SyncedTreeView[PluginDbModel]

    plugin_name_var: StringVar

    def __init__(self, parent: ttk.Widget, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(parent, **kwargs)
        self.plugin_name_var = StringVar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Buttons on top of the list -----------------------------------------
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(column=0, row=0, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        buttons_frame.columnconfigure(0, weight=1)

        def check_for_updates():
            gui_controller.check_for_plugin_updates(self._plugins_list.get_all_objects())

        check_for_updates_button = ttk.Button(buttons_frame, text="Check for updates", command=check_for_updates)
        check_for_updates_button.grid(column=0, row=0, sticky=E, **Config.GLOBAL_GRID_PADDING)

        content_frame = ttk.Frame(self)
        content_frame.grid(column=0, row=1, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Plugins list ----------------------------------------------
        list_frame = ttk.Frame(content_frame)
        list_frame.grid(column=0, row=0, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)

        def get_object_identifier(r: PluginDbModel):
            return r.source

        self._plugins_list = SyncedTreeView(
            get_str_values_fn=plugin_to_str_list,
            get_object_identifier_fn=get_object_identifier,
            master=content_frame,
            columns=plugin_fields,
            show='headings',
            selectmode='browse')
        plugin_list_scrollbar = ttk.Scrollbar(content_frame,
                                              orient="vertical",
                                              command=self._plugins_list.yview)
        plugin_list_scrollbar.grid(column=1, row=0, sticky='NSE')
        self._plugins_list.configure(yscrollcommand=plugin_list_scrollbar.set)
        for plugin_field in plugin_fields:
            self._plugins_list.heading(plugin_field, text=field_name_as_list_header(plugin_field))
        self._plugins_list.grid(column=0, row=0, sticky='NSEW')

        def configure_context_menu(iid: str):
            plugin = self._plugins_list.get_object_by_iid(iid)
            if plugin.state == PluginState.INDEXED:
                self.list_item_context_menu.entryconfigure(0, state=NORMAL)
                self.list_item_context_menu.entryconfigure(1, state=NORMAL)
                self.list_item_context_menu.entryconfigure(2, state=DISABLED)
                self.list_item_context_menu.entryconfigure(3, state=DISABLED)
                self.list_item_context_menu.entryconfigure(4, state=DISABLED)
                self.list_item_context_menu.entryconfigure(5, state=DISABLED)
                self.list_item_context_menu.entryconfigure(6, state=DISABLED)
            elif plugin.state == PluginState.CACHED:
                self.list_item_context_menu.entryconfigure(0, state=DISABLED)
                self.list_item_context_menu.entryconfigure(1, state=DISABLED)
                self.list_item_context_menu.entryconfigure(2, state=NORMAL)
                self.list_item_context_menu.entryconfigure(3, state=NORMAL)
                self.list_item_context_menu.entryconfigure(4, state=DISABLED)
                self.list_item_context_menu.entryconfigure(5, state=DISABLED)
                self.list_item_context_menu.entryconfigure(6, state=DISABLED)
            elif plugin.state == PluginState.INSTALLED:
                self.list_item_context_menu.entryconfigure(0, state=DISABLED)
                self.list_item_context_menu.entryconfigure(1, state=DISABLED)
                self.list_item_context_menu.entryconfigure(2, state=DISABLED)
                self.list_item_context_menu.entryconfigure(3, state=DISABLED)
                self.list_item_context_menu.entryconfigure(4, state=NORMAL)
                self.list_item_context_menu.entryconfigure(5, state=NORMAL)
                if plugin.update_available:
                    self.list_item_context_menu.entryconfigure(6, state=NORMAL)
                else:
                    self.list_item_context_menu.entryconfigure(6, state=DISABLED)

        self.list_item_context_menu = TreeviewContextMenu(self._plugins_list, root, configure_context_menu)

        plugin_details_frame = ttk.Frame(content_frame, )

        plugin_details_frame.grid(column=3, row=0, sticky='NES', **Config.GLOBAL_GRID_PADDING)
        plugin_details_frame.columnconfigure(0, weight=1)
        # plugin_details_frame.rowconfigure(0, weight=1)

        name_label = ttk.Label(plugin_details_frame, text="Name")
        name_label.grid(column=0, row=0, sticky='NEW', **Config.GLOBAL_GRID_PADDING)

        bold_font = font.Font(weight="bold")

        name_text = ttk.Label(plugin_details_frame, textvariable=self.plugin_name_var, font=bold_font)
        name_text.grid(column=0, row=1, sticky='NEW', **Config.GLOBAL_GRID_PADDING)

        def show_plugin_details(ev: Event):
            plugin = self._plugins_list.get_selected_object()
            if plugin is not None:
                self.plugin_name_var.set(plugin.name)

        self._plugins_list.bind("<<TreeviewSelect>>", show_plugin_details)

        def remove_plugin_from_index():  # 0
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.remove_plugin_from_index(plugin)
            self._plugins_list.focus_set()

        self.list_item_context_menu.add_command(label='Remove plugin from index',
                                                command=remove_plugin_from_index,
                                                state=DISABLED)

        def fetch_plugin():  # 1
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.fetch_plugin(plugin)

        self.list_item_context_menu.add_command(label='Fetch plugin',
                                                command=fetch_plugin,
                                                state=DISABLED)

        def delete_plugin_from_cache():  # 2
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.delete_plugin_from_cache(plugin)

        self.list_item_context_menu.add_command(label='Delete plugin from cache',
                                                command=delete_plugin_from_cache)

        def install_plugin_from_cache():  # 3
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.install_plugin_from_cache(plugin)

        self.list_item_context_menu.add_command(label='Install plugin from cache',
                                                command=install_plugin_from_cache)

        def uninstall_plugin():  # 4
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.uninstall_plugin(plugin)

        self.list_item_context_menu.add_command(label='Uninstall plugin',
                                                command=uninstall_plugin)

        def check_for_plugin_update():  # 5
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.check_for_plugin_update(plugin)

        self.list_item_context_menu.add_command(label='Check for plugin update',
                                                command=check_for_plugin_update)

        def update_plugin():  # 6
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.update_plugin(plugin)

        self.list_item_context_menu.add_command(label='Update plugin',
                                                command=update_plugin)

    # Functions for use by GUI controller -----------------------------------------
    def put_plugin(self, plugin: PluginDbModel):
        self._plugins_list.sync_put(plugin)

    def put_plugins(self, plugins: list[PluginDbModel]):
        self._plugins_list.sync_put_all(plugins)

    def clear_plugins(self):
        self._plugins_list.sync_clear()

    def update_plugin(self, plugin: PluginDbModel):
        self._plugins_list.sync_update(plugin)

    def remove_plugin(self, plugin: PluginDbModel):
        self._plugins_list.sync_remove(plugin)
