# -*- coding: utf-8 -*-

from collections import OrderedDict
from copy import deepcopy
from enum import Enum, unique
from math import ceil
import numpy as np
import os
import warnings

import re
import ruamel.yaml as yaml

from monty.serialization import loadfn
from monty.io import zopen

from pymatgen.io.vasp import Potcar, Kpoints, Incar
from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.util.io_utils import clean_lines

from pydefect.core.prior_info import PriorInfo
from pydefect.input_maker.defect_initial_setting import DefectInitialSetting, \
    element_set
from pydefect.database.kpt_centering import kpt_centering
from pydefect.database.atom import symbols_to_atom
from pydefect.util.structure import structure_to_seekpath, find_hpkot_primitive

__author__ = "Yu Kumagai"
__copyright__ = "Copyright 2017, Oba group"
__version__ = "0.1"
__maintainer__ = "Yu Kumagai"
__email__ = "yuuukuma@gmail.com"
__status__ = "Development"
__date__ = "December 4, 2017"

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".pydefect.yaml")
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
INCAR_SETTINGS_FILE = os.path.join(MODULE_DIR, "default_INCAR_setting.yaml")
POTCAR_LIST_FILE = os.path.join(MODULE_DIR, "default_POTCAR_list.yaml")

incar_flags = OrderedDict()
incar_flags["algo"] = ["ALGO"]
incar_flags["accuracy"] = ["PREC", "LREAL", "LASPH", "ENCUT", "NELM", "NELMIN", "EDIFF"]
incar_flags["symmetry"] = ["ISYM", "SYMPREC"]
incar_flags["ionic"] = ["ISIF", "EDIFFG", "IBRION", "NSW"]
incar_flags["occupation"] = ["ISMEAR", "SIGMA", "FERDO", "FERWE", "SMEARINGS"]
incar_flags["magnetization"] = ["ISPIN", "LNONCOLLINEAR", "MAGMOM", "LSORBIT", "GGA_COMPAT"]
incar_flags["mixing"] = ["MIX", "INIMIX", "MAXMIX", "AMIX", "BMIX", "AMIX_MAG", "BMIX_MAG", "AMIN", "MIXPRE", "WC"]
incar_flags["io_control"] = ["ISTART", "ICHARG", "LWAVE", "LCHARG"]
incar_flags["analysis"] = ["NBANDS", "LORBIT", "NEDOS", "EMAX", "EMIN", "RWIGS"]
incar_flags["dielectric"] = ["LEPSILON", "LRPA", "LOPTICS", "LCALCEPS", "EFIELD", "CSHIFT", "OMEGAMIN", "OMEGAMAX", "LNABLA"]
incar_flags["dft"] = ["GGA", "IVDW", "VDW_S6", "VDW_A1", "VDW_S8", "VDW_A2", "METAGGA"]
incar_flags["hybrid"] = ["LHFCALC", "AEXX", "HFSCREEN", "NKRED", "PRECFOCK", "TIME"]
incar_flags["gw"] = ["NBANDSGW", "NOMEGA", "OMEGAMAX", "ANTIRES", "MAXMEM", "NMAXFOCKAE", "NBANDSLF", "ENCUTGW"]
incar_flags["ldau"] = ["LDAU", "LDAUTYPE", "LMAXMIX", "LDAUPRINT", "LDAUL", "LDAUU", "LDAUJ"]
incar_flags["electrostatic"] = ["NELECT", "EPSILON", "DIPOL", "IDIPOL", "LMONO", "LDIPOL"]
incar_flags["parallel"] = ["NPAR", "NCORE", "KPAR"]


@unique
class Task(Enum):
    """
    Supported tasks in pydefect
    """
    structure_opt = "structure_opt"
    band = "band"
    dos = "dos"
    dielectric = "dielectric"
    dielectric_function = "dielectric_function"
    competing_phase = "competing_phase"
    competing_phase_molecule = "competing_phase_molecule"
    defect = "defect"

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s):
        for m in Task:
            if m.name == s:
                return m
        raise AttributeError("Task: " + str(s) + " is not proper.\n" +
                             "Supported Task:\n" + cls.name_list())

    @classmethod
    def name_list(cls):
        return ', '.join([e.value for e in cls])


@unique
class Functional(Enum):
    """
    Supported functionals in pydefect
    """
    pbe = "pbe"
    pbesol = "pbesol"
    pbe_d3 = "pbe_d3"
    hse = "hse"
    nhse = "nhse"
    pbe0 = "pbe0"

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s):
        for m in Functional:
            if m.name == s:
                return m
        raise AttributeError("Functional: " + str(s) + " is not proper.\n" +
                             "Supported Functional:\n" + cls.name_list())

    @classmethod
    def name_list(cls):
        return ', '.join([e.value for e in cls])


class ModIncar(Incar):
    """
    Incar class modified for pretty writing of INCAR file.
    Since from_file and from_string methods in Incar class use Incar class
    constructor, we need to override them.
    """
    @staticmethod
    def from_file(filename):
        """
        Reads an Incar object from a file.

        Args:
            filename (str): Filename for file

        Returns:
            ModIncar object
        """
        with zopen(filename, "rt") as f:
            return ModIncar.from_string(f.read())

    @staticmethod
    def from_string(string):
        """
        Reads an Incar object from a string.

        Args:
            string (str): Incar string

        Returns:
            ModIncar object
        """
        lines = list(clean_lines(string.splitlines()))
        params = {}
        for line in lines:
            m = re.match(r'(\w+)\s*=\s*(.*)', line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                val = Incar.proc_val(key, val)
                params[key] = val
        return ModIncar(params)

    def pretty_write_file(self, filename):
        """
        Write Incar to a file in a prettier manner.

        Args:
            filename (str): filename to write to.
        """

        with zopen(filename, "wt") as fw:
            for key, val in incar_flags.items():
                blank_line = False
                for v in val:
                    if v in self.keys():
                        fw.write(v + " = " + str(self[v]) + "\n")
                        blank_line = True
                if blank_line:
                    fw.write("\n")
        return None


def potcar_dir():
    """
    Returns the name of POTCAR file directory.
    SETTINGS_FILE needs to be defined in the same module.
    """
    pydefect_yaml = None
    potcar_director_path = None
    try:
        with open(SETTINGS_FILE, "r") as f:
            pydefect_yaml = yaml.safe_load(f)
    except IOError:
        print('.pydefect.yaml cannot be opened.')

    for k, v in pydefect_yaml.items():
        if k == "DEFAULT_POTCAR_DIR":
            potcar_director_path = v

    try:
        return potcar_director_path
    except ValueError:
        print('DEFAULT_POTCAR_DIR must be set in .pydefect.yaml')


def make_potcar(elements, potcar="POTCAR"):
    """
    Writes POTCAR with a list of the given element names.
    """

    list_file = loadfn(POTCAR_LIST_FILE)

    with open(potcar, 'w') as pot:
        for e in elements:
            potcar_file_name = \
                os.path.join(potcar_dir(), list_file[e], "POTCAR")

            with open(potcar_file_name) as each_pot:
                pot.write(each_pot.read())


def make_hpkot_primitive_poscar(poscar="POSCAR", pposcar="PPOSCAR",
                                symprec=1e-05, angle_tolerance=-1.0):
    s = Structure.from_file(os.path.join(poscar))
    primitive_structure = find_hpkot_primitive(s, symprec=symprec,
                                               angle_tolerance=angle_tolerance)
    primitive_structure.to(filename=pposcar)


def make_band_kpoints(ibzkpt, dirname='.', poscar="POSCAR",
                      num_split_kpoints=1):
    """
    Write the KPOINTS file for the band structure calculation.
    Args:
        ibzkpt (str): Name of theIBZKPT-type file, which is used to set the
                      weighted k-points.
        dirname (str): Director name at which INCAR is written.
        poscar (str): input POSCAR-type file name
        num_split_kpoints (int): number of KPOINTS files used for a band
                                 structure calculation.
    """

    s = Structure.from_file(os.path.join(poscar))

    seekpath_full_info = structure_to_seekpath(s)

    # primitive structure
    lattice = seekpath_full_info["primitive_lattice"]
    element_types = seekpath_full_info["primitive_types"]
    species = [symbols_to_atom[i] for i in element_types]
    positions = seekpath_full_info["primitive_positions"]
    primitive = Structure(lattice, species, positions)

    # It would be great if sg is obtained from seekpath.
    # Note: Parameters used for the symmetry search are different between
    #       seekpath and pymatgen.
    sg = SpacegroupAnalyzer(structure=primitive).get_space_group_number()

    # k-path
    kpath = seekpath_full_info["explicit_kpoints_rel"]
    kpath_label = seekpath_full_info["explicit_kpoints_labels"]
    ibzkpt = Kpoints.from_file(ibzkpt)

    num_kpoints = ceil(len(kpath) / num_split_kpoints)
    for x in range(num_split_kpoints):
        kpoints = deepcopy(ibzkpt)

        kpoints.comment = \
            "Generated by pydefect. Formula: " + \
            primitive.composition.reduced_formula + " SG: " + str(sg)

        divided_kpath = kpath[num_kpoints * x: num_kpoints * (x + 1)]
        divided_kpath_label = \
            kpath_label[num_kpoints * x: num_kpoints * (x + 1)]

        for d, dl in zip(divided_kpath, divided_kpath_label):
            kpoints.num_kpts += 1
            kpoints.kpts.append(d)
            # weight zero is set here.
            kpoints.kpts_weights.append(0)
            kpoints.labels.append(dl)

        if num_split_kpoints > 1:
            output_filename = os.path.join(dirname, "KPOINTS-" + str(x))
        else:
            output_filename = os.path.join(dirname, "KPOINTS")

        kpoints.write_file(output_filename)


def make_kpoints(task, dirname='.', poscar="POSCAR", num_split_kpoints=1,
                 ibzkpt="IBZKPT", is_metal=False, kpts_shift=None,
                 kpts_density_opt=3, kpts_density_defect=1.5, factor_dos=2,
                 factor_metal=2, prior_info=None):
    """
    Constructs a KPOINTS file based on default settings depending on the task.
    Args:
        task (Task Enum):
        dirname (str): Director name at which INCAR is written.
        poscar (str): input POSCAR-type file name
        num_split_kpoints (int): number of KPOINTS files used for a band
                                 structure calculation.
        ibzkpt (str): Name of the IBZKPT-type file, which is used to set the
                      weighted k-points.
        is_metal (bool): If the system to be calculated is metal or not. This
                         has a meaning for the calculation of a competing phase
        kpts_shift (1x3 list): Shift of k-point set based on vasp setting
        kpts_density_opt (float): Density of k-point = (N_k / k_length) for
                                  structure optimization
        kpts_density_defect (float): Density of k-point = (N_k / k_length) for
                                     point-defect calculations
        factor_dos (int): Multiplier factor for dos and dielectric
            constants.
            This is integer to make k-points even numbers. Then, we can use
            NKRED = 2 for hybrid functional calculations.
        factor_metal (int): Multiplier factor for metallic systems
            This is integer to make k-points even numbers. Then, we can use
            NKRED = 2 for hybrid functional calculations.
        prior_info (str): mp.json file name
    """

    s = Structure.from_file(os.path.join(poscar))
    reciprocal_lattice = s.lattice.reciprocal_lattice

    task = Task.from_string(task)
    comment = "Generated by pydefect. task: " + str(task) + ", "

    if prior_info:
        pi = PriorInfo.load_json(filename=prior_info)
        if pi.is_metal:
            is_metal = True
        if pi.is_molecule:
            task = Task.competing_phase_molecule

    # band
    if task == Task.band:
        make_band_kpoints(ibzkpt, dirname, poscar, num_split_kpoints)
        return True
    # molecule: task is competing_phase_molecule or is_molecule = .True.
    elif task == Task.competing_phase_molecule:
        kpt_mesh = [1, 1, 1]
        comment += "Gamma-only for a cluster."
    # defect
    elif task == Task.defect:
        kpt_mesh = [int(np.ceil(kpts_density_defect * r))
                    for r in reciprocal_lattice.abc]
        comment += "kpt density: " + str(kpts_density_defect)
    else:

        # For primitive cell calculations
        sg = SpacegroupAnalyzer(structure=s).get_space_group_number()

        # Note that the numbers of k-points along all the directions must be the
        # same for body centered orthorhombic and body centered tetragonal to
        # keep the symmetry.
        body_centered_orthorhombic = (23, 24, 44, 45, 46, 71, 72, 73, 74)
        body_centered_tetragonal = (79, 80, 81, 82, 87, 88, 97, 98, 107, 108,
                                    109, 110, 119, 120, 121, 122, 139, 140, 141,
                                    142)
        if sg in body_centered_orthorhombic or body_centered_tetragonal:
            average_abc = np.prod(reciprocal_lattice.abc) ** (1.0 / 3.0)
            revised_reciprocal_abc = (average_abc, average_abc, average_abc)
        else:
            revised_reciprocal_abc = reciprocal_lattice.abc

        # insulating phase
        if task in (Task.competing_phase, Task.structure_opt) \
                and is_metal is False:
            kpt_mesh = [int(np.ceil(kpts_density_opt * r))
                        for r in revised_reciprocal_abc]
            comment += "kpt density: " + str(kpts_density_defect)
        # metallic phase
        elif task == Task.competing_phase and is_metal is True:
            kpt_mesh = [int(np.ceil(kpts_density_opt * r)) * factor_metal
                        for r in revised_reciprocal_abc]
            comment += "kpt density: " + str(kpts_density_defect) + ", " + \
                       "factor: " + str(factor_metal)
        # dos, dielectric const, dielectric function
        elif task in (Task.dos, Task.dielectric, Task.dielectric_function):
            kpt_mesh = [int(np.ceil(kpts_density_opt * r)) * factor_dos
                        for r in revised_reciprocal_abc]
            comment += "kpt density: " + str(kpts_density_defect) + ", " + \
                       "factor: " + str(factor_dos)
        else:
            raise AttributeError("Task: " + str(task) + " is not supported.\n")

    kpts = (tuple(kpt_mesh),)

    if kpts_shift is None:
        if task in (Task.structure_opt, Task.defect):
            angles = s.lattice.angles

            # if not kpts_shift:
            kpts_shift = []
            for i in range(3):
                # shift kpt mesh center only for the lattice vector being normal
                # to a lattice plane and even number of k-points.
                if angles[i - 2] == 90 and angles[i - 1] == 90 \
                        and kpts[0][i] % 2 == 0:
                    kpts_shift.append(0.5)
                else:
                    kpts_shift.append(0.0)

        elif task in (Task.competing_phase_molecule, Task.dos,
                      Task.dielectric, Task.dielectric_function):
            kpts_shift = [0, 0, 0]

        elif task is Task.competing_phase:
            # Check the c-axis for hexagonal phases.
            if 168 <= sg <= 194:
                angles = s.lattice.angles
                if angles[0] != 90 or angles[1] != 90:
                    raise ValueError("Axial in the hexagonal structure is not "
                                     "set properly.")
            kpts_shift = kpt_centering[sg]
            for i in range(3):
                if kpts[0][i] % 2 == 1:
                    kpts_shift[i] = 0

    Kpoints(comment=comment, kpts=kpts, kpts_shift=kpts_shift). \
        write_file(os.path.join(dirname, 'KPOINTS'))


def get_max_enmax(element_names):

    list_file = loadfn(POTCAR_LIST_FILE)
    enmax = []

    for e in element_names:
        potcar_file_name = \
            os.path.join(potcar_dir(), list_file[e], "POTCAR")
        enmax.append(Potcar.from_file(potcar_file_name)[0].enmax)

    return max(enmax)


# TODO: Implement pbe+u
# TODO: NBANDS for band, dos, and dielectric function
# TODO: READ prior_info
def make_incar(task, functional, hfscreen=None, aexx=None, is_metal=False,
               is_magnetization=False, dirname='.', defect_in=None,
               poscar="POSCAR", prior_info=None, my_incar_setting=None):
    """
    Constructs an INCAR file based on default settings depending on the task.
    ENCUT can be determined from max(ENMAX).
    Args:
        task (Task Enum):
        functional (Functional Enum):
        hfscreen (float): VASP parameter of screening distance HFSCREEN
        aexx (float): VASP parameter of the Fock exchange AEXX
        is_metal (bool): If the system to be calculated is metal or not. This
                         has a meaning for the calculation of a competing phase
        is_magnetization (bool):
        dirname (str): Director name at which INCAR is written.
        defect_in (str): defect.in file name parsed for checking elements
        poscar (str): POSCAR-type file name parsed for checking elements
        prior_info (str): prior_info.json file name
        my_incar_setting (str): user setting yaml file name

    defect.in file is parsed when exists, otherwise DPOSCAR file is.
    """

    setting_file = loadfn(INCAR_SETTINGS_FILE)

    task = Task.from_string(task)
    functional = Functional.from_string(functional)

    # raise error when incompatible combinations are given.
    if functional == Functional.nhse and task not in (Task.band, Task.dos):
        raise IncarIncompatibleError(
            "nHSE is not compatible with Task: {}.".format(str(task)))

    setting = {}
    for i in (task, functional):
        try:
            s = setting_file[i.name]
            if s:
                setting.update(s)
        except IOError:
            print('default_INCAR_setting.yaml cannot be opened')

    if is_magnetization:
        setting["ISPIN"] = 2

    # ENCUT is determined by three ways.
    # 1. Parse defect.in file, check relevant elements including foreign atoms
    #    and determine the max ENMAX value.
    # 2. Parse POSCAR file, and check the relevant elements. Note that dopants
    #    are not considered in this case.
    # 3. READ my_incar_setting.yaml file.
    if defect_in:
        defect_initial_setting = \
            DefectInitialSetting.from_defect_in(poscar, defect_in)
        max_enmax = get_max_enmax(element_set(defect_initial_setting))
    elif poscar:
        s = Structure.from_file(poscar)
        elements = s.symbol_set
        max_enmax = get_max_enmax(elements)

    if max_enmax:
        if "ISIF" in setting and setting["ISIF"] > 2:
            setting["ENCUT"] = str(max_enmax * 1.3)
        else:
            setting["ENCUT"] = str(max_enmax)
    else:
        warnings.warn("ENCUT is not set. Add it manually if needed or write it"
                      "in my_incar_setting file.")

    if functional in (Functional.hse, Functional.nhse):
        if hfscreen:
            setting["HFSCREEN"] = hfscreen
        if aexx:
            setting["AEXX"] = aexx

    # read prior_info here.
    if prior_info:
        pi = PriorInfo.load_json(filename=prior_info)
        if pi.is_magnetic:
            setting["ISPIN"] = 2
        if pi.is_metal:
            is_metal = pi.is_metal

    if my_incar_setting:
        setting.update(loadfn(my_incar_setting))

    # From here, we deal with particular issues related to INCAR

    # remove NPAR for the calculations of dielectrics as it is not allowed.
    if task in (Task.dielectric, Task.dielectric_function):
        if "NPAR" in setting:
            setting.pop("NPAR")

    # remove KPAR for band structure calculations
    if task is (Task.band,):
        if "KPAR" in setting:
            setting.pop("NPAR")

    if functional in (Functional.hse, Functional.nhse) \
            and (task in (Task.dos, Task.dielectric_function) or is_metal):
        # the following number should be the same as factor_metal in
        # make_kpoints
        setting["NKRED"] = 2

    incar = os.path.join(dirname, 'INCAR')
    ModIncar(setting).pretty_write_file(filename=incar)

    if functional in (Functional.hse, Functional.nhse):
        incar_pre_gga = os.path.join(dirname, 'INCAR-pre_gga')

        # pop out hybrid related flags.
        for i in incar_flags["hybrid"]:
            if i in setting:
                setting.pop(i)

        # insert some flags.
        setting.update(setting_file["hse_pre"])

        ModIncar(setting).pretty_write_file(filename=incar_pre_gga)


class IncarIncompatibleError(Exception):
    pass
