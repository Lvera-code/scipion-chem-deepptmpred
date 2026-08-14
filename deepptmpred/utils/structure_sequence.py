# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Enzo Sierra (enzogael57@gmail.com)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
"""
Extraction of the ATMSEQ sequence (the sequence actually resolved in the
ATOM records, NOT SEQRES) from a pwchem ``AtomStruct``, already assumed to
be a SINGLE chain (same contract as ``scipion-chem-discotope``/
``scipion-chem-scannet``: chain selection/isolation is the responsibility
of the UPSTREAM protocol -- e.g. ``ProtChemPrepareReceptor`` -- not this
plugin).

Each plugin keeps its own minimal copy of this logic (same policy as
StackGlyEmbed/NetCleave, rather than a shared dependency): residue
resolution via the CCD (``gemmi.find_tabulated_residue``, automatically
resolves modified
residues -- MSE->M, SEP->S, TPO->T, PTR->Y, CSO->C, etc.) instead of
``ResidueSpan.make_one_letter_sequence()`` (can misalign the character
count against the real number of residues on an unrecognized name).
Needed because the DeepPTMPred runner requires an explicit ``--sequence``,
aligned 1:1 with the pose numbering PyRosetta builds when reading the same
PDB (polymer residue N == position N of this sequence).
"""

import gemmi


class StructureSequenceError(Exception):
    pass


def _resolve_residue_letter(resname):
    """Canonical 1-character letter for ``resname`` (3-letter CCD code), or 'X'."""
    info = gemmi.find_tabulated_residue(resname)
    code = info.one_letter_code.strip().upper() if info is not None else ""
    return code if len(code) == 1 and code.isalpha() else "X"


def extract_chain_sequence(pdbPath):
    """ATMSEQ sequence (1 character per residue) of the FIRST polymer chain in ``pdbPath``.

    Assumes a single chain of interest (already isolated upstream) -- if
    the file carries several, uses the first one with a non-empty amino
    acid polymer (same detection criterion as
    ``structure_parser.py::_select_chain``, via ``Chain.get_polymer()``),
    ignoring waters/heteroatoms/ligands.

    Raises:
        StructureSequenceError: if model 1 has no chain with a valid amino
            acid polymer.
    """
    structure = gemmi.read_structure(str(pdbPath))
    structure.setup_entities()

    if len(structure) == 0:
        raise StructureSequenceError(f"'{pdbPath}' does not contain any parseable model (MODEL).")

    model = structure[0]
    chain = None
    for candidate in model:
        if candidate.get_polymer().length() > 0:
            chain = candidate
            break
    if chain is None:
        raise StructureSequenceError(
            f"Model 1 of '{pdbPath}' has no chain with at least one valid amino acid "
            "residue in its polymer."
        )

    residues = list(chain.get_polymer())
    return ''.join(_resolve_residue_letter(residue.name) for residue in residues)
