import math
import unittest
from geometry_tools import circle_tangents,trim_line,extend_line,rectangular_array,polar_array
from model import distance

class V04(unittest.TestCase):
    def test_common_tangents_external_and_internal(self):
        ts=circle_tangents((0,0),5,(30,0),5)
        self.assertEqual(len(ts),4)
        self.assertEqual([t[2] for t in ts].count('External'),2)
        for p,q,kind in ts:
            self.assertAlmostEqual(distance(p,(0,0)),5)
            self.assertAlmostEqual(distance(q,(30,0)),5)
            vec=(q[0]-p[0],q[1]-p[1]);rad=(p[0],p[1])
            self.assertAlmostEqual(vec[0]*rad[0]+vec[1]*rad[1],0,places=5)
    def test_nested_tangents(self):
        self.assertEqual(circle_tangents((0,0),10,(1,0),1),[])
    def test_trim_splits_middle(self):
        line={'type':'line','a':[0,0],'b':[20,0],'layer':'0'}
        boundary=[{'type':'circle','center':[10,0],'radius':3}]
        pieces=trim_line(line,boundary,[10,0])
        self.assertEqual(len(pieces),2)
        self.assertAlmostEqual(pieces[0]['b'][0],7)
        self.assertAlmostEqual(pieces[1]['a'][0],13)
    def test_extend(self):
        line={'type':'line','a':[0,0],'b':[10,0]}
        boundary=[{'type':'line','a':[15,-10],'b':[15,10]}]
        result=extend_line(line,boundary,[9,0]);self.assertAlmostEqual(result['b'][0],15)
    def test_arrays(self):
        e={'type':'circle','center':[10,0],'radius':2,'layer':'0'}
        rect=rectangular_array(e,2,3,5,20)
        self.assertEqual(len(rect),5)
        self.assertEqual(rect[-1]['center'],[20,20])
        polar=polar_array(e,[0,0],4,360)
        self.assertEqual(len(polar),3)
        self.assertAlmostEqual(polar[0]['center'][0],0,places=5)
        self.assertAlmostEqual(polar[0]['center'][1],10,places=5)
    def test_rotated_rectangle_converts_to_polyline(self):
        from geometry_tools import rotate_entity
        e=rotate_entity({'type':'rectangle','a':[0,0],'b':[5,10]},(0,0),45)
        self.assertEqual(e['type'],'polyline')
        self.assertEqual(len(e['points']),4)
if __name__=='__main__':unittest.main()
