# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
import numpy as np

from pymatgen.util.testing import PymatgenTest

from pydefect.core.unitcell_calc_results import UnitcellCalcResults

__author__ = "Yu Kumagai"
__maintainer__ = "Yu Kumagai"

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        "test_files", "core")


class UnitcellDftResultsTest(PymatgenTest):

    def setUp(self):
        """ """
        self.unitcell = UnitcellCalcResults(band_edge=None,
                                            static_dielectric_tensor=None,
                                            ionic_dielectric_tensor=None,
                                            total_dos=None,
                                            volume=None)

        mgo_band_edges = [2.9978, 7.479]
        mgo_static_dielectric_tensor = [[3.166727, 0, 0],
                                        [0, 3.166727, 0],
                                        [0, 0, 3.166727]]
        mgo_ionic_dielectric_tensor = [[9.102401, 0, 0],
                                       [0, 9.102448, 0],
                                       [0, 0, 9.102542]]
        mgo_fictitious_dos = [[0] * 301] * 2
        mgo_fictitious_dos[1][300] = 23.3688

        mgo_volume = 19.1659131591
        self.mgo_unitcell = UnitcellCalcResults(
            band_edge=mgo_band_edges,
            static_dielectric_tensor=mgo_static_dielectric_tensor,
            ionic_dielectric_tensor=mgo_ionic_dielectric_tensor,
            total_dos=mgo_fictitious_dos,
            volume=mgo_volume)

    def test_set_static_dielectric_tensor(self):
        self.unitcell.static_dielectric_tensor = 3.166727
        self.assertArrayAlmostEqual(self.unitcell.static_dielectric_tensor,
                                    self.mgo_unitcell.static_dielectric_tensor)
        self.unitcell.ionic_dielectric_tensor = [9.102401, 9.102448, 9.102542]
        self.assertArrayAlmostEqual(self.unitcell.ionic_dielectric_tensor,
                                    self.mgo_unitcell.ionic_dielectric_tensor)
        # test upper triangle matrix form
        self.unitcell.ionic_dielectric_tensor = [1, 2, 3, 4, 5, 6]
        self.assertArrayAlmostEqual(self.unitcell.ionic_dielectric_tensor,
                                    [[1, 4, 5], [4, 2, 6], [5, 6, 3]])

    def test_band_edge(self):
        self.unitcell.set_band_edge_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/structure_optimization"))
        self.assertArrayAlmostEqual(self.unitcell.band_edge,
                                    self.mgo_unitcell.band_edge)

    def test_dielectric_constant(self):
        self.unitcell.set_static_dielectric_tensor_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/dielectric_constants"))
        self.unitcell.set_ionic_dielectric_tensor_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/dielectric_constants"))
        self.assertArrayAlmostEqual(self.unitcell.static_dielectric_tensor,
                                    self.mgo_unitcell.static_dielectric_tensor)
        self.assertArrayAlmostEqual(self.unitcell.ionic_dielectric_tensor,
                                    self.mgo_unitcell.ionic_dielectric_tensor)
        mgo_total_dielectric_tensor = [[12.269128, 0, 0],
                                       [0, 12.269175, 0],
                                       [0, 0, 12.269269]]
        self.assertArrayAlmostEqual(self.unitcell.total_dielectric_tensor,
                                    mgo_total_dielectric_tensor)

    def test_total_dos(self):
        self.unitcell.set_total_dos_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/structure_optimization"))
        # check length of dos
        self.assertEqual(len(self.unitcell.total_dos[0]), 301)
        # check 301st density of states
        self.assertAlmostEqual(self.unitcell.total_dos[1][300],
                               self.mgo_unitcell.total_dos[1][300])

    def test_volume(self):
        self.unitcell.set_volume_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/structure_optimization"))
        self.assertAlmostEqual(self.unitcell.volume, self.mgo_unitcell.volume)

    def test_dict_json(self):
        self.mgo_unitcell.set_total_dos_from_vasp(
            directory_path=os.path.join(test_dir,
                                        "MgO/unitcell/structure_optimization"))
        tmp_file = tempfile.NamedTemporaryFile()
        self.mgo_unitcell.to_json_file(tmp_file.name)
        unitcell_from_json = UnitcellCalcResults.load_json(tmp_file.name)
        self.assertEqual(unitcell_from_json.as_dict()["total_dos"],
                         self.mgo_unitcell.as_dict()["total_dos"])

    def test_print(self):
        print(self.mgo_unitcell)


if __name__ == "__main__":
    unittest.main()

