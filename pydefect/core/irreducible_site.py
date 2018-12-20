# -*- coding: utf-8 -*-

__author__ = "Yu Kumagai"
__copyright__ = "Copyright 2017, Oba group"
__version__ = "0.1"
__maintainer__ = "Yu Kumagai"
__email__ = "yuuukuma@gmail.com"
__status__ = "Development"
__date__ = "December 4, 2017"


class IrreducibleSite:
    """
    This class object holds properties related to the symmetrically equivalent
    atom set.
    Note1: atomic indices need to be sorted, meaning they can be written in a
           sequence, like 17..32
    Note2: first_index atom is assumed to represent the irreducible atoms.

    Args:
        irreducible_name (str):
            Element name with the irreducible index (e.g., Mg1)
        element (str):
            Element name (e.g., Mg)
        first_index (int):
            First index of irreducible_name.
        last_index (int):
            Last index of irreducible_name.
        representative_coords (list):
            Representative coordinates, namely the position of first_index
        wyckoff (str):
            A wyckoff letter
        site_symmetry (str):
            Site symmetry.
        coordination_distances (dict):
            Coordination environment. An example is
            {"Mg": [1.92, 1.95, 2.01], "Al": [1.82, 1.95]}
    """
    def __init__(self, irreducible_name, element, first_index, last_index,
                 representative_coords, wyckoff=None, site_symmetry=None,
                 coordination_distances=None):
        self._irreducible_name = irreducible_name
        self._element = element
        self._first_index = first_index
        self._last_index = last_index
        self._repr_coords = representative_coords
        self._wyckoff = wyckoff
        self._site_symmetry = site_symmetry
        self._coordination_distances = coordination_distances

    def __eq__(self, other):
        if other is None or type(self) != type(other):
            raise TypeError
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(d["irreducible_name"], d["element"], d["first_index"],
                   d["last_index"], d["repr_coords"], d["wyckoff"],
                   d["site_symmetry"], d["coordination_distances"])

    def as_dict(self):
        d = {"irreducible_name": self._irreducible_name,
             "element": self._element,
             "first_index": self._first_index,
             "last_index": self._last_index,
             "repr_coords": self._repr_coords,
             "wyckoff": self._wyckoff,
             "site_symmetry": self._site_symmetry,
             "coordination_distances": self._coordination_distances}
        return d

    @property
    def irreducible_name(self):
        return self._irreducible_name

    @property
    def element(self):
        return self._element

    @property
    def first_index(self):
        return self._first_index

    @property
    def last_index(self):
        return self._last_index

    @property
    def repr_coords(self):
        return self._repr_coords

    @property
    def wyckoff(self):
        return self._wyckoff

    @property
    def site_symmetry(self):
        return self._site_symmetry

    @property
    def coordination_distances(self):
        return self._coordination_distances

    @property
    def num_atoms(self):
        """
        Returns the number of atoms.
        """
        return self._last_index - self._first_index + 1
