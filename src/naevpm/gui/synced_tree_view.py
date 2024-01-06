from tkinter import ttk
from typing import Callable, TypeVar, Generic, Optional

from naevpm.gui.tk_iid_object_sync import TkIidObjSync

T = TypeVar('T')


class SyncedTreeView(ttk.Treeview, Generic[T]):
    _sync: TkIidObjSync
    _get_str_values_fn: Callable[[T], list[str]]

    def __init__(self, get_str_values_fn: Callable[[T], list[str]],
                 get_object_identifier_fn: Callable[[T], str], master, takefocus=True, **kw):
        super().__init__(master, takefocus=takefocus, **kw)
        self._get_str_values_fn = get_str_values_fn
        self._sync = TkIidObjSync(get_object_identifier_fn)

        # Set rowheight explicitly to prevent squashed rows
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview", rowheight=30)

        def focus_el(ev):
            selection = self.selection()
            if len(selection) > 0:
                self.focus(self.selection()[0])

        self.bind("<FocusIn>", focus_el)

    def sync_put(self, obj: T):
        iid = self.insert('', 'end', values=self._get_str_values_fn(obj))
        self._sync.put(iid, obj)
        if iid != '':
            self.selection_set(iid)

    def sync_put_all(self, objects: list[T]):
        self.sync_clear()
        first = True
        for obj in objects:
            iid = self.insert('', 'end', values=self._get_str_values_fn(obj))
            self._sync.put(iid, obj)
            if iid != '' and first:
                self.selection_set(iid)
                first = False

    def sync_clear(self):
        self._sync.clear()
        self.delete(*self.get_children())

    def sync_update(self, obj: T):
        iid = self._sync.get_iid_by_object(obj)
        self.item(iid, values=self._get_str_values_fn(obj))

    def sync_remove(self, obj: T):
        iid = self._sync.remove_by_object(obj)
        sibling = self.prev(iid)
        if sibling == '':
            sibling = self.next(iid)
        if sibling != '':
            self.selection_set(sibling)
            self.focus(sibling)
        self.delete(iid)

    def get_object_by_iid(self, iid: str) -> T:
        return self._sync.get_object_by_iid(iid)

    def get_iid_by_object(self, obj: T) -> str:
        return self._sync.get_iid_by_object(obj)

    def get_all_objects(self) -> list[T]:
        return self._sync.get_all_objects()

    def get_all_item_iids(self) -> list[str]:
        return self._sync.get_all_item_iids()

    def get_selected_object(self) -> Optional[T]:
        selected_iids = self.selection()
        if len(selected_iids) > 0:
            return self._sync.get_object_by_iid(selected_iids[0])
        return None

    def get_selected_iid(self) -> str:
        selected_iids = self.selection()
        if len(selected_iids) > 0:
            return selected_iids[0]

    def is_empty(self) -> bool:
        return self._sync.is_empty()

    def get_last_iid(self) -> Optional[str]:
        return self._sync.get_last_iid()