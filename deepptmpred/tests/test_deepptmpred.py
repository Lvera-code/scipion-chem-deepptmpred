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

from pwem.protocols import ProtImportPdb
from pwchem.protocols import ProtChemPrepareReceptor
from pyworkflow.tests import BaseTest, setupTestProject

from ..protocols import ProtDeepPTMPredPrediction

# 7c4s downloaded live from RCSB (not a hardcoded local file), same fixture
# already used by scipion-chem-discotope/scipion-chem-scannet.
_TEST_PDB_ID = '7c4s'
# Same real mmCIF label_asym_id vs auth_asym_id gotcha already documented in
# scipion-chem-discotope/discotope/tests/test_discotope.py -- 'C' is the
# label_asym_id that corresponds to the real author chain 'A' (the antigen,
# 283 residues), NOT 'A' (which in label_asym_id is the antibody's light
# chain, 214 residues). Do not "simplify" this back to 'A'.
_TEST_CHAIN = 'C'


class TestDeepPTMPredPrediction(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setupTestProject(cls)

        cls.protImportPdb = cls._runImportPdb()
        cls.protPrepareReceptor = cls._runPrepareReceptorChain(cls.protImportPdb)

    @classmethod
    def _runImportPdb(cls):
        protImportPdb = cls.newProtocol(ProtImportPdb, inputPdbData=0, pdbId=_TEST_PDB_ID)
        cls.proj.launchProtocol(protImportPdb, wait=True)
        return protImportPdb

    @classmethod
    def _runPrepareReceptorChain(cls, protImportPdb):
        # usePDBFixer=True (force real legacy PDB output, needed because
        # DeepPTMPred uses PyRosetta/Bio.PDB on a legacy PDB, not mmCIF) and
        # addRes=False (avoids PDBFixer --add-residues' non-deterministic
        # conformational sampling) -- same real arguments already validated
        # in scipion-chem-discotope for exactly this same problem.
        protPrepareReceptor = cls.newProtocol(
            ProtChemPrepareReceptor,
            inputAtomStruct=protImportPdb.outputPdb,
            usePDBFixer=True, addRes=False, HETATM=False, rchains=True,
            chain_name='{"model": 0, "chain": "%s"}' % _TEST_CHAIN,
        )
        cls.proj.launchProtocol(protPrepareReceptor, wait=True)
        return protPrepareReceptor

    def _runDeepPTMPredPrediction(self):
        protDeepPTMPred = self.newProtocol(ProtDeepPTMPredPrediction)
        protDeepPTMPred.inputStructure.set(self.protPrepareReceptor)
        protDeepPTMPred.inputStructure.setExtended('outputStructure')
        self.launchProtocol(protDeepPTMPred, wait=True)
        return protDeepPTMPred

    def test(self):
        protDeepPTMPred = self._runDeepPTMPredPrediction()
        outROIs = getattr(protDeepPTMPred, 'outputROIs', None)
        self.assertIsNotNone(outROIs)
