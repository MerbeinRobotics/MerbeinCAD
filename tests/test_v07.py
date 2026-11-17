import unittest, tempfile
from pathlib import Path
from model import Document
from solid3d import profile_points,make_solid,project

class V07Tests(unittest.TestCase):
    def test_extrude(self):
        e={'type':'rectangle','a':[0,0],'b':[20,10]}
        verts,edges=make_solid(e,'extrude',5)
        self.assertEqual(len(verts),8)
        self.assertEqual(len(edges),12)
        self.assertEqual(verts[-1][-1],5)
    def test_revolve(self):
        e={'type':'rectangle','a':[5,0],'b':[10,10]}
        verts,edges=make_solid(e,'revolve',360,'Y',steps=12)
        self.assertEqual(len(verts),48)
        self.assertTrue(len(edges)>80)
    def test_profile_reject_open(self):
        with self.assertRaises(ValueError):profile_points({'type':'line','a':[0,0],'b':[2,3]})
    def test_projection(self):
        self.assertEqual(len(project([3,2,1])),2)
    def test_save_legacy_compat(self):
        doc=Document();doc.entities=[{'type':'point3d','xyz':[1,2,3]}]
        doc.solids=[{'profile':{'type':'rectangle','a':[0,0],'b':[2,2]},'operation':'extrude','amount':3}]
        doc.layer_styles={'0':{'color':'#abcdef','linetype':'CENTER'}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.mrcad';doc.save(p);loaded=Document.load(p)
            self.assertEqual(loaded.solids,doc.solids)
            self.assertEqual(loaded.entities,doc.entities)
            self.assertEqual(loaded.layer_styles,doc.layer_styles)
if __name__=='__main__':unittest.main()

class V07ExportTests(unittest.TestCase):
    def test_dxf_layer_style_dimension_offset_and_point3d(self):
        from exporters import export_dxf
        try:import ezdxf
        except ImportError:self.skipTest('ezdxf not installed')
        doc=Document()
        doc.layer_styles={'0':{'linetype':'CENTER','color':'#38bdf8'}}
        doc.entities=[{'type':'dimension','a':[0,0],'b':[20,0],'offset':8,'layer':'0'},
                      {'type':'point3d','xyz':[1,2,3],'layer':'0'}]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'drawing.dxf';export_dxf(doc,p)
            dwg=ezdxf.readfile(p)
            self.assertEqual(dwg.layers.get('0').dxf.linetype,'CENTER')
            self.assertEqual(sum(1 for e in dwg.modelspace() if e.dxftype()=='POINT'),1)
            lines=[e for e in dwg.modelspace() if e.dxftype()=='LINE']
            self.assertEqual(len(lines),3)
            self.assertTrue(any(abs(l.dxf.start.y-8)<1e-9 and abs(l.dxf.end.y-8)<1e-9 for l in lines))
    def test_cadquery_solid_export_if_installed(self):
        try:import cadquery
        except ImportError:self.skipTest('CadQuery not installed')
        from solid3d import export_solid_step
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'solids.step'
            solids=[{'profile':{'type':'rectangle','a':[0,0],'b':[20,10]},'operation':'extrude','amount':5},
                    {'profile':{'type':'rectangle','a':[5,0],'b':[9,15]},'operation':'revolve','axis':'Y','amount':360}]
            self.assertEqual(export_solid_step(solids,p),2)
            self.assertGreater(p.stat().st_size,1000)
