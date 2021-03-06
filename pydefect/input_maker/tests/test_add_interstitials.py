import os
from pathlib import Path
from shutil import copyfile

from pydefect.input_maker.add_interstitials import add_interstitials
from pydefect.util.testing import PydefectTest

parent = Path(__file__).parent


class AddInterstitialsTest(PydefectTest):
    def test(self):
        copyfile(parent / "test_add_interstitials.yaml", "interstitials.yaml")
        add_interstitials(
            coords_in_unitcell=[0.25, 0.25, 0.25],
            vicinage_radius=1.0,
            uposcar=str(self.POSCARS_DIR / "POSCAR-MgO"),
            interstitials_yaml=str("interstitials.yaml"))

    def tearDown(self) -> None:
        try:
            os.remove("interstitials.yaml")
        except FileNotFoundError:
            pass

