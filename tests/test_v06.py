"""Version 0.6 regression coverage (GUI exercised separately under virtual display)."""
import unittest
from pathlib import Path
from updater import compare_version, clean_repo
from geometry_v05 import group_polar_array


class V06(unittest.TestCase):
    def test_release_versions(self):
        self.assertGreater(compare_version('v0.6','0.5'),0)
        self.assertEqual(compare_version('v0.6','0.6'),0)

    def test_repository(self):
        self.assertEqual(clean_repo('https://github.com/MerbeinRobotics/MerbeinCAD'),
                         'MerbeinRobotics/MerbeinCAD')

    def test_polar_center_selected_with_snap(self):
        circle={'type':'circle','center':[25,0],'radius':3,'layer':'0'}
        # array centre is a supplied drawing point, not a fixed origin.
        items=group_polar_array([circle],[5,0],4,360)
        self.assertEqual(len(items),3)
        self.assertAlmostEqual(items[0]['center'][0],5.0)
        self.assertAlmostEqual(items[0]['center'][1],20.0)

    def test_installer_assets_present(self):
        base=Path(__file__).resolve().parents[1]
        self.assertTrue((base/'Install_MerbeinCAD.ps1').is_file())
        self.assertTrue((base/'Install_MerbeinCAD.bat').is_file())
        self.assertTrue((base/'tooltips_v06.py').is_file())

if __name__=='__main__':unittest.main()
