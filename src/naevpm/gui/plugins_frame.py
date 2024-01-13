from tkinter import ttk, E, DISABLED, NORMAL, StringVar, Event, font, NO, HORIZONTAL

from naevpm.core.config import Config
from naevpm.core.models import indexed_plugin_fields, IndexedPluginDbModel, PluginState, PluginMetadataDbModel
from naevpm.gui.abstract_gui_controller import AbstractGuiController
from naevpm.gui.data_model_to_str_list import plugin_to_str_list
from naevpm.gui.display_utils import field_name_as_list_header
from naevpm.gui.synced_tree_view import SyncedTreeView
from naevpm.gui.tk_root import TkRoot
from naevpm.gui.treeview_context_menu import TreeviewContextMenu


class PluginsFrame(ttk.Frame):
    _plugins_list: SyncedTreeView[IndexedPluginDbModel]

    plugin_name_var: StringVar
    plugin_author_var: StringVar
    plugin_version_var: StringVar
    plugin_description_var: StringVar

    def __init__(self, parent: ttk.Widget, root: TkRoot, gui_controller: AbstractGuiController, **kwargs):
        super().__init__(parent, **kwargs)
        self.plugin_name_var = StringVar()
        self.plugin_author_var = StringVar()
        self.plugin_version_var = StringVar()
        self.plugin_description_var = StringVar()
        # Workaround to set a minimum height of the plugin details frame
        self.plugin_description_var.set("-----------------------------------------" * 15)
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

        paned_window = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned_window.grid(column=0, row=1, sticky='NSEW', **Config.GLOBAL_GRID_PADDING)

        # Plugins list ----------------------------------------------
        list_frame = ttk.Frame(paned_window)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        paned_window.add(list_frame, weight=1)

        def get_object_identifier(r: IndexedPluginDbModel):
            return r.source

        self._plugins_list = SyncedTreeView(
            get_str_values_fn=plugin_to_str_list,
            get_object_identifier_fn=get_object_identifier,
            master=list_frame,
            columns=indexed_plugin_fields,
            show='headings',
            selectmode='browse')
        plugin_list_scrollbar = ttk.Scrollbar(list_frame,
                                              orient="vertical",
                                              command=self._plugins_list.yview)
        plugin_list_scrollbar.grid(column=1, row=0, sticky='NSE')
        self._plugins_list.configure(yscrollcommand=plugin_list_scrollbar.set)
        for plugin_field in indexed_plugin_fields:
            self._plugins_list.heading(plugin_field, text=field_name_as_list_header(plugin_field))
            if plugin_field == 'state':
                self._plugins_list.column(plugin_field, minwidth=0, width=70, stretch=NO)
            elif plugin_field == 'update_available':
                self._plugins_list.column(plugin_field, minwidth=0, width=120, stretch=NO)
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

        plugin_details_frame = ttk.Frame(paned_window)
        plugin_details_frame.columnconfigure(0, weight=1)
        paned_window.add(plugin_details_frame, weight=1)

        bold_font = font.Font(weight="bold")

        name_label = ttk.Label(plugin_details_frame, text="Name")
        name_label.grid(column=0, row=0, sticky='NEW')
        # The width for the label seems to work. It sets a minimum width for the plugin
        # details frame
        name_text = ttk.Label(plugin_details_frame, textvariable=self.plugin_name_var, font=bold_font,
                              wraplength=300, width=30)
        name_text.grid(column=0, row=1, sticky='NEW')

        author_label = ttk.Label(plugin_details_frame, text="Author(s)")
        author_label.grid(column=0, row=2, sticky='NEW')
        author_text = ttk.Label(plugin_details_frame, textvariable=self.plugin_author_var, font=bold_font,
                                wraplength=300)
        author_text.grid(column=0, row=3, sticky='NEW')

        version_label = ttk.Label(plugin_details_frame, text="Version")
        version_label.grid(column=0, row=4, sticky='NEW')
        version_text = ttk.Label(plugin_details_frame, textvariable=self.plugin_version_var, font=bold_font,
                                 wraplength=300)
        version_text.grid(column=0, row=5, sticky='NEW')

        description_label = ttk.Label(plugin_details_frame, text="Description")
        description_label.grid(column=0, row=6, sticky='NEW')
        description_text = ttk.Label(plugin_details_frame, textvariable=self.plugin_description_var, font=bold_font,
                                     wraplength=300)
        description_text.grid(column=0, row=7, sticky='NEW')

        # noinspection PyUnusedLocal
        def show_plugin_details(ev: Event):
            plugin = self._plugins_list.get_selected_object()
            if plugin is not None and plugin.state in [PluginState.CACHED, PluginState.INSTALLED]:
                gui_controller.show_plugin_details(plugin)
            else:
                self.plugin_name_var.set(' ' * 80)
                self.plugin_author_var.set(' ' * 80)
                self.plugin_version_var.set(' ' * 80)
                self.plugin_description_var.set(' ' * 80)

        self._plugins_list.bind("<<TreeviewSelect>>", show_plugin_details)

        def remove_plugin_from_index():  # 0
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.remove_plugin(plugin)
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
            gui_controller.delete_plugin(plugin)

        self.list_item_context_menu.add_command(label='Delete plugin from cache',
                                                command=delete_plugin_from_cache)

        def install_plugin_from_cache():  # 3
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.install_plugin(plugin)

        self.list_item_context_menu.add_command(label='Install plugin from cache',
                                                command=install_plugin_from_cache)

        def uninstall_plugin():  # 4
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.uninstall_plugin(plugin)

        self.list_item_context_menu.add_command(label='Uninstall plugin',
                                                command=uninstall_plugin)

        def check_for_plugin_update():  # 5
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.check_plugin(plugin)

        self.list_item_context_menu.add_command(label='Check for plugin update',
                                                command=check_for_plugin_update)

        def update_plugin():  # 6
            plugin = self._plugins_list.get_object_by_iid(self.list_item_context_menu.item_id)
            gui_controller.update_plugin(plugin)

        self.list_item_context_menu.add_command(label='Update plugin',
                                                command=update_plugin)

    # Functions for use by GUI controller -----------------------------------------
    def put_plugin(self, plugin: IndexedPluginDbModel):
        self._plugins_list.sync_put(plugin)

    def put_plugins(self, plugins: list[IndexedPluginDbModel]):
        self._plugins_list.sync_put_all(plugins)

    def clear_plugins(self):
        self._plugins_list.sync_clear()

    def update_plugin(self, plugin: IndexedPluginDbModel):
        self._plugins_list.sync_update(plugin)

    def remove_plugin(self, plugin: IndexedPluginDbModel):
        self._plugins_list.sync_remove(plugin)

    def show_plugin_details(self, plugin: IndexedPluginDbModel, plugin_meta_data: PluginMetadataDbModel):
        if self._plugins_list.get_selected_object() is plugin and plugin_meta_data is not None:
            self.plugin_name_var.set(plugin_meta_data.name)
            self.plugin_author_var.set(plugin_meta_data.author)
            self.plugin_version_var.set(plugin_meta_data.version)
            self.plugin_description_var.set(plugin_meta_data.description)
