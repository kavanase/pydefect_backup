# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from pymatgen.core.structure import Structure

from pydefect.input_maker.defect_initial_setting import extended_range, \
    get_electronegativity, get_oxidation_state, print_dopant_info, \
    DefectInitialSetting
from pydefect.core.irreducible_site import IrreducibleSite

__author__ = "Yu Kumagai"
__copyright__ = "Copyright 2017, Oba group"
__version__ = "0.1"
__maintainer__ = "Yu Kumagai"
__email__ = "yuuukuma@gmail.com"
__status__ = "Development"
__date__ = "December 4, 2017"

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        "test_files", "input_maker")


class ExtendedRangeTest(unittest.TestCase):
    def test_range(self):
        expected_positive = [0, 1, 2, 3]
        actual_positive = [i for i in extended_range(3)]
        self.assertEqual(actual_positive, expected_positive)

        expected_negative = [-3, -2, -1, 0]
        actual_negative = [i for i in extended_range(-3)]
        self.assertEqual(actual_negative, expected_negative)


class GetElectronegativityTest(unittest.TestCase):
    def test_success(self):
        true_element = "Mg"
        expected = 1.31
        self.assertEqual(get_electronegativity(true_element), expected)

    def test_fail(self):
        fake_element = "Yk"
        expected = None
        self.assertEqual(get_electronegativity(fake_element), expected)


class GetOxidationStateTest(unittest.TestCase):
    def test_success(self):
        true_element = "Mg"
        expected = 2
        self.assertEqual(get_oxidation_state(true_element), expected)

    def test_fail(self):
        fake_element = "Yk"
        expected = None
        self.assertEqual(get_oxidation_state(fake_element), expected)


# TODO: write test_print_dopant_info
class PrintDopantInfoTest(unittest.TestCase):
    pass


class DefectInitialSettingTest(unittest.TestCase):

    def setUp(self):
        """
        The following condition can be generated by typing
        python3 defect_initial_setting.py -p POSCAR-MgO64atoms -d Al N
        --included Va_O1_-1 Va_O1_-2 --excluded Va_O1_1 Va_O1_2 --distance 0.15
        --symprec 0.001 --cutoff 2.0 -e 4 -i 0.1 0.1 0.1
        """
        structure = Structure.\
            from_file(os.path.join(test_dir, "POSCAR-MgO64atoms"))

        Mg1 = IrreducibleSite(irreducible_name="Mg1",
                              element="Mg",
                              first_index=1,
                              last_index=32,
                              representative_coords=[0, 0, 0])
        O1 = IrreducibleSite(irreducible_name="O1",
                             element="O",
                             first_index=33,
                             last_index=64,
                             representative_coords=[0.25, 0.25, 0.25])
        irreducible_sites = [Mg1, O1]

        dopant_configs = [["Al", "Mg"], ["Al", "O"], ["N", "Mg"], ["N", "O"]]
        antisite_configs = [["Mg", "O"], ["O", "Mg"]]
        interstitial_coords = [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]]
        included = ["Va_O1_-1", "Va_O1_-2"]
        excluded = ["Va_O1_1", "Va_O1_2"]
        distance = 0.15
        cutoff = 2.0
        symprec = 0.001
        oxidation_states = {"Mg": 2, "O": -2, "Al": 3, "N": -3}
        electronegativity = {"Mg": 1.31, "O": 3.44, "Al": 1.61, "N": 3.04}

        self._mgo = DefectInitialSetting(structure,
                                         irreducible_sites,
                                         dopant_configs,
                                         antisite_configs,
                                         interstitial_coords,
                                         included,
                                         excluded,
                                         distance,
                                         cutoff,
                                         symprec,
                                         oxidation_states,
                                         electronegativity)

    def test_dict(self):
        # object -> dict -> object
        mgo_dict = self._mgo.as_dict()
        mgo_from_dict = DefectInitialSetting.from_dict(mgo_dict)

        # irreducible_sites usually return pointers, __eq__ is overloaded in
        # defect_initial_setting.py. So, no problem for comparison.
        self.assertTrue(vars(mgo_from_dict) == vars(self._mgo))

    def test_to_json_file(self):
        # object -> json file -> object
        with tempfile.NamedTemporaryFile() as fp:
            tmp_json = fp.name
            self._mgo.to_json_file(tmp_json)
            mgo_from_json = DefectInitialSetting.json_load(tmp_json)
            print(vars(mgo_from_json))
            self.assertTrue(vars(mgo_from_json) == vars(self._mgo))

    def test_from_defect_in(self):
        mgo_from_defect_in = \
            DefectInitialSetting.from_defect_in(
                poscar=os.path.join(test_dir, "POSCAR-MgO64atoms"),
                defect_in_file=os.path.join(test_dir, "defect.in.example"))

        self.assertTrue(vars(mgo_from_defect_in) == vars(self._mgo))

    def test_from_basic_settings(self):
        mgo_from_basic_settings = \
            DefectInitialSetting.from_basic_settings(
                poscar=os.path.join(test_dir, "POSCAR-MgO64atoms"),
                dopants=["Al", "N"],
                flattened_interstitial_coords=[0.1, 0.1, 0.1, 0.2, 0.2, 0.2],
                is_antisite=True,
                en_diff=4.0,
                included=["Va_O1_-1", "Va_O1_-2"],
                excluded=["Va_O1_1", "Va_O1_2"],
                distance=0.15,
                cutoff=2.0,
                symprec=0.001)

        self.assertTrue(mgo_from_basic_settings == self._mgo)

    def test_make_defect_name_set(self):
        # Sequence of expected is changed for easy view. Thus, sort is needed
        # for comparison.
        expected = \
            ['Va_Mg1_-2', 'Va_Mg1_-1', 'Va_Mg1_0', 'Va_O1_0', 'Mg_i1_0',
             'Mg_i1_1', 'Mg_i1_2', 'Mg_i2_0', 'Mg_i2_1', 'Mg_i2_2', 'O_i1_-2',
             'O_i1_-1', 'O_i1_0', 'O_i2_-2', 'O_i2_-1', 'O_i2_0', 'N_i1_-3',
             'N_i1_-2', 'N_i1_-1', 'N_i1_0', 'N_i2_-3', 'N_i2_-2', 'N_i2_-1',
             'N_i2_0', 'Al_i1_0', 'Al_i1_1', 'Al_i1_2', 'Al_i1_3', 'Al_i2_0',
             'Al_i2_1', 'Al_i2_2', 'Al_i2_3', 'Mg_O1_0', 'Mg_O1_1', 'Mg_O1_2',
             'Mg_O1_3', 'Mg_O1_4', 'O_Mg1_-4', 'O_Mg1_-3', 'O_Mg1_-2',
             'O_Mg1_-1', 'O_Mg1_0', 'Al_Mg1_0', 'Al_Mg1_1', 'Al_O1_0',
             'Al_O1_1', 'Al_O1_2', 'Al_O1_3', 'Al_O1_4', 'Al_O1_5', 'N_Mg1_-5',
             'N_Mg1_-4', 'N_Mg1_-3', 'N_Mg1_-2', 'N_Mg1_-1', 'N_Mg1_0',
             'N_O1_-1', 'N_O1_0', 'Va_O1_-1', 'Va_O1_-2']

        actual = self._mgo.make_defect_name_set()
        self.assertEqual(sorted(actual), sorted(expected))


if __name__ == "__main__":
    unittest.main()