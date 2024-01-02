from tkinter import ttk, E, DISABLED, NORMAL

from naevpm.core.config import Config
from naevpm.core.models import plugin_fields, PluginDbModel, PluginState
from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.display_utils import field_name_as_list_header, display_boolean
from naevpm.gui.tk_root import TkRoot
from naevpm.gui.treeview_context_menu import TreeviewContextMenu


class PluginsFrame(ttk.Frame):
    _plugins_list: ttk.Treeview
    _iid_plugin_map: dict[str, PluginDbModel]
    _source_iid_map: dict[str, str]
    _plugins: list[PluginDbModel]

    def __init__(self, parent: ttk.Widget, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(parent, **kwargs)

        self._iid_plugin_map = {}
        self._source_iid_map = {}
        self._plugins = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Buttons on top of the list -----------------------------------------
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(column=0, row=0, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        buttons_frame.columnconfigure(0, weight=1)

        def check_for_updates():
            gui_controller.check_for_plugin_updates(self._plugins)

        check_for_updates_button = ttk.Button(buttons_frame, text="Check for updates", command=check_for_updates)
        check_for_updates_button.grid(column=0, row=0, sticky=E, **Config.GLOBAL_GRID_PADDING)

        # Plugins list ----------------------------------------------
        list_frame = ttk.Frame(self)
        list_frame.grid(column=0, row=1, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._plugins_list = ttk.Treeview(list_frame, columns=plugin_fields, show='headings')
        plugin_list_scrollbar = ttk.Scrollbar(list_frame,
                                              orient="vertical",
                                              command=self._plugins_list.yview)
        plugin_list_scrollbar.grid(column=1, row=0, sticky='NSE')
        self._plugins_list.configure(yscrollcommand=plugin_list_scrollbar.set)
        for plugin_field in plugin_fields:
            self._plugins_list.heading(plugin_field, text=field_name_as_list_header(plugin_field))
        self._plugins_list.grid(column=0, row=0, sticky='NSEW')

        def configure_context_menu(iid: str):
            plugin = self._iid_plugin_map[iid]
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

        def remove_plugin_from_index():  # 0
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.remove_plugin_from_index(plugin)

        self.list_item_context_menu.add_command(label='Remove plugin from index',
                                                command=remove_plugin_from_index,
                                                state=DISABLED)

        def fetch_plugin():  # 1
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.fetch_plugin(plugin)

        self.list_item_context_menu.add_command(label='Fetch plugin',
                                                command=fetch_plugin,
                                                state=DISABLED)

        def delete_plugin_from_cache():  # 2
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.delete_plugin_from_cache(plugin)

        self.list_item_context_menu.add_command(label='Delete plugin from cache',
                                                command=delete_plugin_from_cache)

        def install_plugin_from_cache():  # 3
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.install_plugin_from_cache(plugin)

        self.list_item_context_menu.add_command(label='Install plugin from cache',
                                                command=install_plugin_from_cache)

        def uninstall_plugin():  # 4
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.uninstall_plugin(plugin)

        self.list_item_context_menu.add_command(label='Uninstall plugin',
                                                command=uninstall_plugin)

        def check_for_plugin_update():  # 5
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.check_for_plugin_update(plugin)

        self.list_item_context_menu.add_command(label='Check for plugin update',
                                                command=check_for_plugin_update)

        def update_plugin():  # 6
            plugin = self._iid_plugin_map[self.list_item_context_menu.item_id]
            gui_controller.update_plugin(plugin)

        self.list_item_context_menu.add_command(label='Update plugin',
                                                command=update_plugin)

    def _plugin_values(self, plugin: PluginDbModel) -> list[str]:
        values = []
        obj = plugin.__dict__
        for plugin_field in plugin_fields:
            if plugin_field == 'installed' or \
                    plugin_field == 'cached' or \
                    plugin_field == 'update_available':
                values.append(display_boolean(obj[plugin_field]))
            elif plugin_field == 'state':
                values.append(plugin.state.name)
            else:
                values.append(obj[plugin_field])
        return values

    # Functions for use by GUI controller -----------------------------------------
    def insert_plugin(self, plugin: PluginDbModel):
        iid = self._plugins_list.insert('', 'end', values=self._plugin_values(plugin))
        self._iid_plugin_map[iid] = plugin
        self._source_iid_map[plugin.source] = iid
        self._plugins.append(plugin)

    def set_plugins(self, plugins: list[PluginDbModel]):
        self.clear_plugins()
        for plugin in plugins:
            self.insert_plugin(plugin)

    def clear_plugins(self):
        self._plugins_list.delete(*self._plugins_list.get_children())
        self._iid_plugin_map = {}
        self._source_iid_map = {}
        self._plugins = []

    def set_plugin(self, plugin: PluginDbModel):
        iid = self._source_iid_map[plugin.source]
        self._plugins_list.item(iid, values=self._plugin_values(plugin))

    def remove_plugin(self, plugin: PluginDbModel):
        iid = self._source_iid_map[plugin.source]
        self._plugins_list.delete(iid)

        del self._iid_plugin_map[iid]
        del self._source_iid_map[plugin.source]
        self._plugins.remove(plugin)
