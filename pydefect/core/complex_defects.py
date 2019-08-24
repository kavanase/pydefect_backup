# -*- coding: utf-8 -*-

from copy import deepcopy
from collections import OrderedDict
from typing import Optional, List, Union

import yaml
from monty.json import MSONable
from pydefect.core.config import SYMMETRY_TOLERANCE, ANGLE_TOL
from pydefect.core.interstitial_site import represent_odict, construct_odict
from pydefect.util.logger import get_logger
from pymatgen.core.structure import Structure
from pydefect.util.structure_tools import count_equivalent_clusters

__author__ = "Yu Kumagai"
__maintainer__ = "Yu Kumagai"

"""

"""

logger = get_logger(__name__)

# See document in interstitial_site.py
yaml.add_representer(OrderedDict, represent_odict)
yaml.add_constructor('tag:yaml.org,2002:map', construct_odict)


class ComplexDefect(MSONable):
    """Holds properties related to a complex defect. """

    def __init__(self,
                 removed_atom_indices: list,
                 inserted_atoms: List[dict],
                 point_group: str,
                 multiplicity: int,
                 extreme_charge_state: int,
                 annotation: Optional[str] = None):
        """
        Args:
            removed_atom_indices (list):
                List of removed atom indices in supercell perfect structure.
            inserted_atoms (List):
                List of dict with "element" and "coords" keys.
                Not that "index" is absent as it is not determined, yet.
            point_group (str):
                point group
            multiplicity (int):
                Multiplicity of the complex defect in supercell perfect structure.
            annotation (str):
                Annotation used when analyzing results.
            extreme_charge_state (int):

        """
        self.removed_atom_indices = removed_atom_indices[:]
        self.inserted_atoms = inserted_atoms[:]
        self.point_group = point_group
        self.multiplicity = multiplicity
        self.extreme_charge_state = extreme_charge_state
        self.annotation = annotation

    def __repr__(self):
        outs = [f"extreme charge state: {self.extreme_charge_state}",
                f"annotation: {self.annotation}"]
        return "\n".join(outs)

    def as_dict(self):
        d = OrderedDict(
            {"removed_atom_indices": self.removed_atom_indices,
             "inserted_atoms":       self.inserted_atoms,
             "point_group":          self.point_group,
             "multiplicity":         self.multiplicity,
             "extreme_charge_state": self.extreme_charge_state,
             "annotation":           self.annotation})

        return d


class ComplexDefects(MSONable):
    """Holds a set of InterstitialSite objects. """

    def __init__(self,
                 structure: Structure,
                 complex_defects: OrderedDict = None):
        """
        Args:
            structure (Structure):
                Structure class object. Supercell used for defect
                calculations.
            complex_defects (OrderedDict):
                OrderedDict with keys of defect names and values of
                ComplexDefect objects.
        """
        self.structure = structure
        if complex_defects is not None:
            self.complex_defects = deepcopy(complex_defects)
        else:
            self.complex_defects = OrderedDict()

    def set_as_dict(self):
        d = OrderedDict()
        for k, v in self.complex_defects.items():
            d[k] = v.as_dict()

        return d

    def site_set_to_yaml_file(self,
                              yaml_filename: str = "complex_defects.yaml"):
        with open(yaml_filename, "w") as f:
            f.write(yaml.dump(self.set_as_dict()))

    def to_yaml_file(self,
                     yaml_filename: str = "complex_defects.yaml"):
        with open(yaml_filename, "w") as f:
            f.write(yaml.dump(self.as_dict()))

    @classmethod
    def from_files(cls,
                   structure: Union[str, Structure] = "DPOSCAR",
                   yaml_filename: str = "complex_defects.yaml"):
        if isinstance(structure, str):
            d = {"structure": Structure.from_file(structure)}
        else:
            d = {"structure": structure}

        with open(yaml_filename, "r") as f:
            d["complex_defects"] = yaml.load(f)

        return cls.from_dict(d)

    @classmethod
    def from_dict(cls, d: dict):
        # orderedDict disables MSONable.
        structure = d["structure"]
        if isinstance(structure, dict):
            structure = Structure.from_dict(structure)

        complex_defects = OrderedDict()
        for k, v in d["complex_defects"].items():
            complex_defects[k] = ComplexDefect.from_dict(v)

        return cls(structure=structure, complex_defects=complex_defects)

    def add_defect(self,
                   removed_atom_indices: list,
                   inserted_atoms: List[dict],
                   name: Optional[str] = None,
                   extreme_charge_state: Optional[int] = None,
                   annotation: Optional[str] = None,
                   symprec: float = SYMMETRY_TOLERANCE,
                   angle_tolerance: float = ANGLE_TOL) -> None:

        inserted_atom_coords = [i["coords"] for i in inserted_atoms]
        multiplicity, point_group = \
            count_equivalent_clusters(self.structure,
                                      inserted_atom_coords,
                                      removed_atom_indices,
                                      symprec,
                                      angle_tolerance)

        complex_defect = \
            ComplexDefect(removed_atom_indices, inserted_atoms,
                          point_group, multiplicity, extreme_charge_state,
                          annotation)

        self.complex_defects[name] = complex_defect

