import os
import sys
import tempfile
import unittest
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from model import Document,move_entity,bounding_box,distance

class ModelTest(unittest.TestCase):
    def test_round_trip(self):
        d=Document([{'type':'rectangle','a':[0,0],'b':[100,50],'layer':'0'}])
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'test.mrcad');d.save(path);loaded=Document.load(path)
            self.assertEqual(d.entities,loaded.entities)
    def test_move(self):
        e={'type':'circle','center':[4,6],'radius':5}
        self.assertEqual(move_entity(e,2,-3)['center'],[6,3]);self.assertEqual(e['center'],[4,6])
    def test_bounds(self):
        self.assertEqual(bounding_box([{'type':'circle','center':[0,0],'radius':10}]),(-10,-10,10,10))

if __name__=='__main__':unittest.main()
