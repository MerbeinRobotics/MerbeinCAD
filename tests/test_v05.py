import unittest
import math
from geometry_v05 import corner_edit, group_rectangular_array, group_polar_array, edited_group
from model import distance

class V05(unittest.TestCase):
    def setUp(self):
        self.horizontal={'type':'line','a':[0,0],'b':[30,0]}
        self.vertical={'type':'line','a':[0,0],'b':[0,30]}
    def test_chamfer(self):
        a,b,join=corner_edit(self.horizontal,self.vertical,5)
        self.assertEqual(a['a'],[5.,0.])
        self.assertEqual(b['a'],[0.,5.])
        self.assertEqual(join['type'],'line')
    def test_fillet(self):
        a,b,arc=corner_edit(self.horizontal,self.vertical,5,True)
        self.assertAlmostEqual(a['a'][0],5)
        self.assertAlmostEqual(b['a'][1],5)
        self.assertEqual(len(arc['points']),33)
        self.assertAlmostEqual(distance(arc['points'][0],[5,5]),5)
        self.assertAlmostEqual(distance(arc['points'][-1],[5,5]),5)
    def test_invalid_fillet(self):
        with self.assertRaises(ValueError):corner_edit(self.horizontal,self.vertical,35,True)
    def test_parallel_lines(self):
        with self.assertRaises(ValueError):corner_edit(self.horizontal,{'type':'line','a':[0,10],'b':[30,10]},3)
    def test_group_array(self):
        group=[self.horizontal,self.vertical]
        self.assertEqual(len(group_rectangular_array(group,2,3,30,20)),10)
        self.assertEqual(len(group_polar_array(group,[0,0],4)),6)
    def test_move_copy_rotate(self):
        output=edited_group([self.horizontal],10,0,90,[0,0])
        self.assertAlmostEqual(output[0]['a'][0],0,places=6)
        self.assertAlmostEqual(output[0]['a'][1],10,places=6)

if __name__=='__main__':unittest.main()
