# -*- coding: utf-8 -*-

from collections import namedtuple
import numpy as np
import os
import tempfile
import unittest
from copy import deepcopy

from pydefect.analysis.defect_energies import DefectEnergies, Defect
from pydefect.analysis.defect_concentration import DefectConcentration
from pydefect.analysis.defect_energy_plotter import DefectEnergyPlotter
from pydefect.analysis.chempotdiag.chem_pot_diag import ChemPotDiag
from pydefect.core.correction import Correction
from pydefect.core.supercell_dft_results import SupercellDftResults
from pydefect.core.unitcell_dft_results import UnitcellDftResults
from pydefect.core.defect_entry import DefectEntry

__author__ = "Yu Kumagai"
__copyright__ = "Copyright 2017, Oba group"
__version__ = "0.1"
__maintainer__ = "Yu Kumagai"
__email__ = "yuuukuma@gmail.com"
__status__ = "Development"
__date__ = "Feb. 25, 2018"

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        "test_files", "core")


class DefectEnergiesTest(unittest.TestCase):

    def setUp(self):
        """ """
        unitcell_file = os.path.join(test_dir, "MgO/defects/unitcell.json")
        unitcell = UnitcellDftResults.load_json(unitcell_file)
        perfect_file = os.path.join(test_dir,
                                    "MgO/defects/perfect/dft_results.json")
        perfect = SupercellDftResults.load_json(perfect_file)

        defect_dirs = ["Mg_O1_0", "Mg_O1_1", "Mg_O1_2", "Mg_O1_3", "Mg_O1_4",
                       "Mg_i1_0", "Mg_i1_1", "Mg_i1_2", "Va_O1_1", "Va_O1_2",
                       "Va_O1_0"]
        defects = []
        for dd in defect_dirs:
            d = os.path.join(test_dir, "MgO/defects", dd)
            defect_entry = \
                DefectEntry.load_json(os.path.join(d, "defect_entry.json"))
            dft_results = \
                SupercellDftResults.load_json(
                    os.path.join(d, "dft_results.json"))
            correction = \
                Correction.load_json(os.path.join(d, "correction.json"))

            defect = Defect(defect_entry=defect_entry,
                            dft_results=dft_results,
                            correction=correction)

            defects.append(defect)

        # temporary insert values
        chem_pot = ChemPotDiag.load_vertices_yaml(
            os.path.join(test_dir, "MgO/vertices_MgO.yaml"))

        chem_pot_label = "A"

        self.defect_energies = \
            DefectEnergies.from_files(unitcell=unitcell,
                                      perfect=perfect,
                                      defects=defects,
                                      chem_pot=chem_pot,
                                      chem_pot_label=chem_pot_label,
                                      system="MgO")

        temperature = 10000
        temperature2 = 1000
        num_sites_filename = os.path.join(test_dir,
                                          "MgO/defects/num_sites.yaml")

        dc1 = DefectConcentration.from_defect_energies(
            defect_energies=self.defect_energies,
            temperature=temperature,
            unitcell=unitcell,
            num_sites_filename=num_sites_filename)

        self.dc2 = DefectConcentration.from_defect_energies(
            defect_energies=self.defect_energies,
            temperature=temperature2,
            unitcell=unitcell,
            num_sites_filename=num_sites_filename,
            previous_concentration=dc1,
            verbose=False)

    def test_calc_transition_levels(self):
        dp = DefectEnergyPlotter(self.defect_energies, self.dc2)
#        plt = dp.plot_energy(filtering_words=["Va_O[0-9]+"],
        plt = dp.plot_energy(show_transition_levels=True,
                             show_fermi_level=True,
                             show_all_lines=True)
        plt.show()
#        plt.savefig(fname="energy.eps")

if __name__ == "__main__":
    unittest.main()
