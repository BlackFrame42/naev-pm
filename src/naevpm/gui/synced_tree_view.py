from tkinter import ttk
from typing import Callable, TypeVar

from naevpm.gui.tk_iid_object_sync import TkIidObjSync

T = TypeVar('T')


class SyncedTreeView(ttk.Treeview):
    _sync: TkIidObjSync
    _get_str_values_fn: Callable[[T], list[str]]

    def __init__(self, get_str_values_fn: Callable[[T], list[str]],
                 get_object_identifier_fn: Callable[[T], str], master, **kw):
        super().__init__(master, **kw)
        self._get_str_values_fn = get_str_values_fn
        self._sync = TkIidObjSync(get_object_identifier_fn)

    def sync_put(self, obj: T):
        iid = self.insert('', 'end', values=self._get_str_values_fn(obj))
        self._sync.put(iid, obj)

    def sync_put_all(self, objects: list[T]):
        self.sync_clear()
        for obj in objects:
            self.sync_put(obj)

    def sync_clear(self):
        self._sync.clear()
        self.delete(*self.get_children())

    def sync_update(self, obj: T):
        iid = self._sync.get_iid_by_object(obj)
        self.item(iid, values=self._get_str_values_fn(obj))

    def sync_remove(self, obj: T):
        iid = self._sync.remove_by_object(obj)
        self.delete(iid)

    def get_object_by_iid(self, iid: str) -> T:
        return self._sync.get_object_by_iid(iid)

    def get_iid_by_object(self, obj: T) -> str:
        return self._sync.get_iid_by_object(obj)

    def get_all_objects(self) -> list[T]:
        return self._sync.get_all_objects()

    def get_all_item_iids(self) -> list[str]:
        return self._sync.get_all_item_iids()
