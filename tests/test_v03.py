import unittest
from snapping import circle_line_intersections,circle_circle_intersections,tangent_points,nearest_snap
from updater import compare_version,clean_repo

class NewGeometryTests(unittest.TestCase):
    def test_line_circle_intersection(self):
        got=circle_line_intersections((0,0),5,(-10,0),(10,0))
        self.assertEqual(sorted(round(p[0],3) for p in got),[-5,5])
    def test_circle_circle_intersection(self):
        got=circle_circle_intersections((0,0),5,(8,0),5)
        self.assertEqual(sorted(round(p[1],3) for p in got),[-3,3])
    def test_external_tangent(self):
        got=tangent_points((10,0),(0,0),5)
        self.assertEqual(len(got),2)
        for x,y in got:
            self.assertAlmostEqual(x,2.5)
            self.assertAlmostEqual(x*x+y*y,25)
            self.assertAlmostEqual((10-x)*x+(0-y)*y,0)
    def test_tangent_nearest(self):
        doc=[{'type':'circle','center':[0,0],'radius':5}]
        result=nearest_snap((2.5,4.330127),doc,1,{'Tangent'},anchor=(10,0))
        self.assertEqual(result.kind,'Tangent')
    def test_snap_circle_intersection(self):
        doc=[{'type':'line','a':[-10,0],'b':[10,0]},{'type':'circle','center':[0,0],'radius':5}]
        result=nearest_snap((5.1,0.1),doc,1,{'Intersection'})
        self.assertEqual(result.kind,'Intersection')
        self.assertAlmostEqual(result.point[0],5)
    def test_versions(self):
        self.assertEqual(compare_version('v0.4','0.3'),1)
        self.assertEqual(compare_version('v0.3.0','0.3'),0)
        self.assertEqual(compare_version('v0.2','0.3'),-1)
    def test_repo(self):
        self.assertEqual(clean_repo('https://github.com/org/MerbeinCAD'),'org/MerbeinCAD')
        with self.assertRaises(ValueError):clean_repo('https://evil.example/x/y')

if __name__=='__main__':unittest.main()
