from typing import Callable, TypeVar, Optional

T = TypeVar('T')


class TkIidObjSync:
    _iid_to_object_map: dict[str, T] = {}
    _obj_id_to_iid_map: dict[str, str] = {}
    _objects: list[T] = []

    _get_obj_id_fn: Callable[[T], str]

    def __init__(self, get_obj_id_fn: Callable[[T], str]):
        super().__init__()
        self._get_obj_id_fn = get_obj_id_fn

    def put(self, iid: str, obj: T):
        existing_obj = self._iid_to_object_map.get(iid, None)
        obj_id = self._get_obj_id_fn(obj)
        existing_iid = self._obj_id_to_iid_map.get(obj_id, None)
        if existing_obj is not None or existing_iid is not None:
            if existing_iid == iid and existing_obj is obj:
                # ignore already added iid and obj pair
                return
            else:
                raise ValueError("The iid or obj is already mapped to another iid or obj."
                                 "In other words: Any item identifier or object can only be"
                                 "added once."
                                 "This is likely a programming error as this should never happen.")
        self._obj_id_to_iid_map[obj_id] = iid
        self._iid_to_object_map[iid] = obj
        self._objects.append(obj)

    def remove_by_object(self, obj: T) -> str:
        obj_id = self._get_obj_id_fn(obj)
        iid = self._obj_id_to_iid_map[obj_id]
        del self._obj_id_to_iid_map[obj_id]
        del self._iid_to_object_map[iid]
        self._objects.remove(obj)
        return iid

    def remove_by_iid(self, iid: str):
        obj = self._iid_to_object_map[iid]
        obj_id = self._get_obj_id_fn(obj)
        del self._obj_id_to_iid_map[obj_id]
        del self._iid_to_object_map[iid]
        self._objects.remove(obj)

    def clear(self):
        self._iid_to_object_map = {}
        self._obj_id_to_iid_map = {}
        self._objects = []

    def get_object_by_iid(self, iid: str) -> T:
        return self._iid_to_object_map[iid]

    def get_iid_by_object(self, obj: T) -> str:
        obj_id = self._get_obj_id_fn(obj)
        return self._obj_id_to_iid_map[obj_id]

    def get_all_objects(self) -> list[T]:
        return self._objects

    def get_all_item_iids(self) -> list[str]:
        return list(self._iid_to_object_map.keys())

    def is_empty(self) -> bool:
        return len(self._objects) == 0

    def get_last_iid(self) -> Optional[str]:
        iids = self.get_all_item_iids()
        if len(iids) > 0:
            return iids[-1]
        return None
