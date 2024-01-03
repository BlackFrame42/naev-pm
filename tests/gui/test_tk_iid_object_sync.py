import unittest

from naevpm.core.models import PluginDbModel, PluginState
from naevpm.gui.tk_iid_object_sync import TkIidObjSync


class TestTkItemIdentifierObjectSync(unittest.TestCase):

    def test_upper(self):
        def get_obj_identifier(obj: PluginDbModel):
            return obj.source

        sync = TkIidObjSync(get_obj_identifier)
        obj1 = PluginDbModel('name1', 'source1', PluginState.INDEXED)
        obj2 = PluginDbModel('name2', 'source2', PluginState.INDEXED)
        obj3 = PluginDbModel('name3', 'source3', PluginState.INDEXED)
        sync.put('id1', obj1)
        sync.put('id2', obj2)
        sync.put('id3', obj3)
        self.assertIs(sync.get_object_by_iid('id1'), obj1)
        self.assertIs(sync.get_object_by_iid('id2'), obj2)
        self.assertIs(sync.get_object_by_iid('id3'), obj3)
        self.assertEqual(sync.get_iid_by_object(obj1), 'id1')
        self.assertEqual(sync.get_iid_by_object(obj2), 'id2')
        self.assertEqual(sync.get_iid_by_object(obj3), 'id3')
        objects = sync.get_all_objects()
        self.assertIs(objects[0], obj1)
        self.assertIs(objects[1], obj2)
        self.assertIs(objects[2], obj3)
        iids = sync.get_all_item_iids()
        self.assertEqual(iids[0], 'id1')
        self.assertEqual(iids[1], 'id2')
        self.assertEqual(iids[2], 'id3')
        sync.remove_by_object(obj1)
        sync.remove_by_object(obj2)
        sync.remove_by_object(obj3)
        self.assertEqual(len(sync.get_all_objects()), 0)
        self.assertEqual(len(sync.get_all_item_iids()), 0)

        sync.put('id1', obj1)
        sync.put('id2', obj2)
        sync.put('id3', obj3)
        self.assertIs(sync.get_object_by_iid('id1'), obj1)
        self.assertIs(sync.get_object_by_iid('id2'), obj2)
        self.assertIs(sync.get_object_by_iid('id3'), obj3)
        self.assertEqual(sync.get_iid_by_object(obj1), 'id1')
        self.assertEqual(sync.get_iid_by_object(obj2), 'id2')
        self.assertEqual(sync.get_iid_by_object(obj3), 'id3')
        objects = sync.get_all_objects()
        self.assertIs(objects[0], obj1)
        self.assertIs(objects[1], obj2)
        self.assertIs(objects[2], obj3)
        iids = sync.get_all_item_iids()
        self.assertEqual(iids[0], 'id1')
        self.assertEqual(iids[1], 'id2')
        self.assertEqual(iids[2], 'id3')
        sync.remove_by_iid('id1')
        sync.remove_by_iid('id2')
        sync.remove_by_iid('id3')
        self.assertEqual(len(sync.get_all_objects()), 0)
        self.assertEqual(len(sync.get_all_item_iids()), 0)

        sync.put('id1', obj1)
        sync.put('id2', obj2)
        sync.put('id3', obj3)
        self.assertIs(sync.get_object_by_iid('id1'), obj1)
        self.assertIs(sync.get_object_by_iid('id2'), obj2)
        self.assertIs(sync.get_object_by_iid('id3'), obj3)
        self.assertEqual(sync.get_iid_by_object(obj1), 'id1')
        self.assertEqual(sync.get_iid_by_object(obj2), 'id2')
        self.assertEqual(sync.get_iid_by_object(obj3), 'id3')
        objects = sync.get_all_objects()
        self.assertIs(objects[0], obj1)
        self.assertIs(objects[1], obj2)
        self.assertIs(objects[2], obj3)
        iids = sync.get_all_item_iids()
        self.assertEqual(iids[0], 'id1')
        self.assertEqual(iids[1], 'id2')
        self.assertEqual(iids[2], 'id3')
        sync.clear()
        self.assertEqual(len(sync.get_all_objects()), 0)
        self.assertEqual(len(sync.get_all_item_iids()), 0)

        sync.put('id1', obj1)
        sync.put('id1', obj1)
        self.assertEqual(len(sync.get_all_objects()), 1)
        self.assertEqual(len(sync.get_all_item_iids()), 1)

        try:
            sync.put('id1', obj1)
            sync.put('id1', obj2)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            sync.put('id1', obj1)
            sync.put('id2', obj1)
            self.assertTrue(False)
        except ValueError:
            pass


if __name__ == '__main__':
    unittest.main()
