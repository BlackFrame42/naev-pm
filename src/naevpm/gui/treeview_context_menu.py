from tkinter import Menu, ttk
from typing import Optional, Callable

from naevpm.gui.tk_root import TkRoot


class TreeviewContextMenu(Menu):
    _parent: ttk.Treeview
    root: TkRoot
    _scheduled_hide_id: Optional[str] = None
    item_id: str
    pre_show_fn: Callable

    def mouse_entered(self):
        if self._scheduled_hide_id is not None:
            self.root.after_cancel(self._scheduled_hide_id)

    def hide(self):
        self._parent.tk.call(self._parent, "tag", "remove", "highlight-for-context-menu")
        self.unpost()

    def mouse_left(self):
        if self._scheduled_hide_id is not None:
            self.root.after_cancel(self._scheduled_hide_id)
        self._scheduled_hide_id = self.root.after(500, lambda: self.hide())

    def show(self, event):
        iid = self._parent.identify_row(event.y)
        if iid != '':
            self.pre_show_fn(iid)
            self._parent.tk.call(self._parent, "tag", "remove", "highlight-for-context-menu")
            self._parent.tk.call(self._parent, "tag", "add", "highlight-for-context-menu", iid)
            self.item_id = iid
            row = self._parent.set(iid)
            # Ignore empty lines
            if row != {}:
                self.post(event.x_root, event.y_root)
                # Hide menu unless immediately entered
                self.mouse_left()

    def __init__(self, parent: ttk.Treeview, root: TkRoot, pre_show_fn: Callable[[str], None], **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self.root = root
        self.pre_show_fn = pre_show_fn
        parent.tag_configure('highlight-for-context-menu', background='lightblue')

        self.bind('<Leave>', lambda ev: self.mouse_left())
        self.bind('<Enter>', lambda ev: self.mouse_entered())

        if root.windowing_system == 'aqua':
            parent.bind('<2>', lambda ev: self.show(ev))
            parent.bind('<Control-1>', lambda ev: self.show(ev))
        else:
            parent.bind('<3>', lambda ev: self.show(ev))
