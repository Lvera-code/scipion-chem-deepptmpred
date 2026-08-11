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
Extraccion de secuencia ATMSEQ (la secuencia realmente resuelta en los
registros ATOM, NO SEQRES) desde un ``AtomStruct`` de pwchem, ya asumido de
UNA sola cadena (mismo contrato que ``scipion-chem-discotope``/
``scipion-chem-scannet``: la seleccion/aislamiento de cadena es
responsabilidad del protocolo AGUAS ARRIBA -- p.ej. ``ProtChemPrepareReceptor``
-- no de este plugin).

Logica vendorizada (misma politica de "cada plugin mantiene su propia copia
minima" que StackGlyEmbed/NetCleave) a partir de
``PTM-Prediction/src/utils/structure_parser.py``, ya validada end-to-end en
el pipeline standalone: resolucion de residuos via CCD
(``gemmi.find_tabulated_residue``, resuelve automaticamente residuos
modificados -- MSE->M, SEP->S, TPO->T, PTR->Y, CSO->C, etc.) en vez de
``ResidueSpan.make_one_letter_sequence()`` (puede desalinear el conteo de
caracteres frente al numero real de residuos ante un nombre no reconocido).
Necesaria porque el runner de DeepPTMPred exige ``--sequence`` explicita,
alineada 1:1 con la numeracion de pose que PyRosetta construye leyendo el
mismo PDB (residuo N del polimero == posicion N de esta secuencia).
"""

import gemmi


class StructureSequenceError(Exception):
    pass


def _resolve_residue_letter(resname):
    """Letra canonica de 1 caracter para ``resname`` (codigo CCD de 3 letras), o 'X'."""
    info = gemmi.find_tabulated_residue(resname)
    code = info.one_letter_code.strip().upper() if info is not None else ""
    return code if len(code) == 1 and code.isalpha() else "X"


def extract_chain_sequence(pdbPath):
    """Secuencia ATMSEQ (1 caracter por residuo) de la PRIMERA cadena polimero de ``pdbPath``.

    Asume una unica cadena de interes (ya aislada aguas arriba) -- si el
    archivo trae varias, usa la primera con un polimero de aminoacidos no
    vacio (mismo criterio de deteccion que ``structure_parser.py::_select_chain``,
    via ``Chain.get_polymer()``), ignorando aguas/heteroatomos/ligandos.

    Raises:
        StructureSequenceError: si el modelo 1 no tiene ninguna cadena con
            un polimero de aminoacidos valido.
    """
    structure = gemmi.read_structure(str(pdbPath))
    structure.setup_entities()

    if len(structure) == 0:
        raise StructureSequenceError(f"'{pdbPath}' no contiene ningun modelo (MODEL) parseable.")

    model = structure[0]
    chain = None
    for candidate in model:
        if candidate.get_polymer().length() > 0:
            chain = candidate
            break
    if chain is None:
        raise StructureSequenceError(
            f"El modelo 1 de '{pdbPath}' no tiene ninguna cadena con al menos un residuo de "
            "aminoacido valido en su polimero."
        )

    residues = list(chain.get_polymer())
    return ''.join(_resolve_residue_letter(residue.name) for residue in residues)
