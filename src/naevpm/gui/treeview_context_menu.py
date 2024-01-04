from tkinter import Menu, ttk
from typing import Optional, Callable

from naevpm.gui.tk_root import TkRoot


class TreeviewContextMenu(Menu):
    _parent: ttk.Treeview
    root: TkRoot
    _scheduled_hide_id: Optional[str] = None
    item_id: str
    pre_show_fn: Callable

    def hide(self):
        self._parent.tk.call(self._parent, "tag", "remove", "highlight-for-context-menu")
        self.unpost()
        self._parent.focus_set()

    def show(self, event):
        iid = self._parent.identify_row(event.y)
        self.show_on(iid, event.x_root, event.y_root)

    def show_on(self, iid: str, x, y):
        if iid != '':
            self.pre_show_fn(iid)
            self._parent.tk.call(self._parent, "tag", "remove", "highlight-for-context-menu")
            self._parent.tk.call(self._parent, "tag", "add", "highlight-for-context-menu", iid)
            self.item_id = iid
            row = self._parent.set(iid)
            # Ignore empty lines
            if row != {}:
                self.post(x, y)
                self.focus()

    def __init__(self, parent: ttk.Treeview, root: TkRoot, pre_show_fn: Callable[[str], None], **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self.root = root
        self.pre_show_fn = pre_show_fn
        parent.tag_configure('highlight-for-context-menu', background='lightblue')

        if root.windowing_system == 'aqua':
            parent.bind('<2>', lambda ev: self.show(ev))
            parent.bind('<Control-1>', lambda ev: self.show(ev))
        else:
            parent.bind('<3>', lambda ev: self.show(ev))

        self.bind("<FocusOut>", lambda ev: self.hide())
        self.bind("<Escape>", lambda ev: self.hide())
        self.bind("<Left>", lambda ev: self.hide())

        def show_menu_under_row():
            iid = self._parent.focus()
            if iid != '':
                bbox = self._parent.bbox(iid)
                treeview_x = self._parent.winfo_rootx()
                treeview_y = self._parent.winfo_rooty()
                self.show_on(iid, treeview_x + bbox[0], treeview_y+bbox[1]+bbox[3])

        self._parent.bind("<Menu>", lambda ev: show_menu_under_row())
        self._parent.bind("<Right>", lambda ev: show_menu_under_row())
