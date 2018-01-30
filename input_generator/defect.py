#!/usr/bin/env python

__author__ = "Yu Kumagai"
__copyright__ = "Copyright 2017, Oba group"
__version__ = "0.1"
__maintainer__ = "Yu Kumagai"
__email__ = "yuuukuma@gmail.com"
__status__ = "Development"
__date__ = "December 4, 2017"

class IrreducibleSite():
    """
    This class object holds properties related to irreducible atom set.
    Note1: atomic indices need to be sorted. Thus, they can be written in one 
           sequence.
    Note2: first_index atom is assumed to represent the irreducible atoms.

    Args:
        irreducible_name (str): element name with irreducible index (e.g., Mg1)
        element (str): element name (e.g., Mg)
        first_index (int): first index of irreducible_name. 
        last_index (int): last index of irreducible_name. 
        repr_coords (array): representative coordinates, namely the position
                            of first_index

    TODO1: Add the site symmetry information.
    """
    def __init__(self, irreducible_name, element, first_index, last_index, 
                 repr_coords):
        self.irreducible_name = irreducible_name
        self.element = element
        self.first_index = first_index
        self.last_index = last_index
        self.repr_coords = repr_coords

    def __eq__(self, other):
        if other is None or type(self) != type(other): 
            raise TypeError
        return self.__dict__ == other.__dict__

    def as_dict(self):
        d = {"irreducible_name": self.irreducible_name,
             "element" : self.element,
             "first_index" : self.first_index,
             "last_index" : self.last_index,
             "repr_coords" : self.repr_coords}
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(d["irreducible_name"], d["element"], d["first_index"], 
                   d["last_index"], d["repr_coords"]) 

    @property
    def natoms(self):
        """
        Return number of atoms in a given (super)cell.
        """
        return self.last_index - self.first_index + 1
