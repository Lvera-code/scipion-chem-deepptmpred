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
This protocol predicts post-translational modification (PTM) sites on a
single-chain protein structure using a local DeepPTMPred installation.
"""

import csv
import os

from pwchem.objects import Sequence, SequenceROI, SetOfSequenceROIs
from pwem.protocols import EMProtocol
from pyworkflow.object import Boolean, Float, String
from pyworkflow.protocol import params

from .. import Plugin as deepptmpredPlugin
from ..constants import CALIBRATED_THRESHOLDS, DEFAULT_MIN_PROBABILITY, PTM_TYPES
from ..utils.structure_sequence import extract_chain_sequence

OUTPUT_COLUMNS = ['protein_id', 'position', 'residue', 'probability', 'ptm_type']


class ProtDeepPTMPredPrediction(EMProtocol):
    """
    AI Generated:

    Predicts PTM candidate sites (17 types: phosphorylation, acetylation,
    ubiquitination, hydroxylation, gamma-carboxyglutamic acid, lysine/
    arginine methylation, malonylation, crotonylation, succinylation,
    glutathionylation, sumoylation, S-nitrosylation, glutarylation,
    citrullination, O/N-linked glycosylation) from a single-chain protein
    STRUCTURE, using a local DeepPTMPred installation (PyRosetta structural
    features -- SASA, phi/psi, local plDDT -- combined with ESM-2
    embeddings). Structure-only: unlike DeepMVP, DeepPTMPred requires a PDB
    (no sequence-only mode), so it is only usable when a structure is
    available; a downstream ``scipion-chem-ptmannotation`` protocol fuses
    its output with DeepMVP into a consensus call.

    Invokes DeepPTMPred once PER PTM TYPE (17 subprocess calls, one .h5
    model each -- DeepPTMPred has no single multi-type CLI, unlike
    DeepMVP), via a vendorized runner (``scripts/deepptmpred_runner.py``,
    see its own docstring for the 3 real scientific patches it applies on
    top of the vendored ``predict.py``).

    Positions are 1-based over the ATMSEQ extracted directly from the input
    structure (NOT a separately-uploaded FASTA) -- for the consensus in
    ``ProtPTMAnnotation`` to align with DeepMVP's own positions, DeepMVP
    must be run on a ``Sequence`` derived from THIS SAME single-chain
    structure.

    Output
    ------
    outputROIs: SetOfSequenceROIs, one SequenceROI per candidate site
    (single-residue ROI, ``roiIdx == roiIdx2``). Each ROI carries ``_type``
    (canonical PTM type name), ``_scoreDeepptmpred`` (raw probability),
    ``_passesThreshold`` (probability >= the type's own calibrated
    threshold -- NOT a single global cutoff, see ``constants.CALIBRATED_THRESHOLDS``)
    and ``_meanScore`` (project-wide ranking convention, same value as
    ``_scoreDeepptmpred``).
    """

    _label = 'deepptmpred ptm prediction'

    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('inputStructure', params.PointerParam, pointerClass='AtomStruct',
                       label='Input structure (single chain): ',
                       help='Single-chain PDB structure to scan for PTM candidate sites. Must '
                            'contain exactly one polymer chain (isolate it upstream, e.g. with '
                            "pwchem's ProtChemPrepareReceptor, the same convention as "
                            'scipion-chem-discotope/scipion-chem-scannet).')
        form.addParam('timeoutSeconds', params.IntParam, default=3600,
                       label='Timeout (s) per PTM type: ', expertLevel=params.LEVEL_ADVANCED,
                       help='Maximum time a single PTM-type invocation is allowed to run before '
                            'the step is aborted as failed. Increase on slow/CPU-only hardware.')

    def _insertAllSteps(self):
        self._insertFunctionStep(self.deepptmpredStep)
        self._insertFunctionStep(self.createOutputStep)

    # ---------------------------------- Steps -----------------------------------

    def deepptmpredStep(self):
        pdbPath = os.path.abspath(self.inputStructure.get().getFileName())
        sequence = extract_chain_sequence(pdbPath)
        proteinId = os.path.splitext(os.path.basename(pdbPath))[0]

        # ABSOLUTE paths are mandatory: the subprocess runs with
        # cwd=train_ptm_dir, so a relative path from self._getExtraPath()
        # would resolve against that wrong cwd, not the Scipion project
        # root (same pattern as scipion-chem-deepmvp).
        esmCacheDir = os.path.abspath(self._getExtraPath('esm_cache'))
        os.makedirs(esmCacheDir, exist_ok=True)

        for ptmType in PTM_TYPES:
            outCsv = os.path.abspath(self._getExtraPath(f'{ptmType}.csv'))
            args = (
                f'--train-ptm-dir {deepptmpredPlugin.getTrainPtmDir()} '
                f'--protein-id {proteinId} --sequence {sequence} --pdb-path {pdbPath} '
                f'--ptm-type {ptmType} --esm-checkpoint {deepptmpredPlugin.getEsmCheckpointPath()} '
                f'--custom-esm-dir {esmCacheDir} --out-csv {outCsv}'
            )
            deepptmpredPlugin.runDeepPTMPred(self, args, cwd=deepptmpredPlugin.getTrainPtmDir())

    def createOutputStep(self):
        pdbPath = os.path.abspath(self.inputStructure.get().getFileName())
        sequence = extract_chain_sequence(pdbPath)
        stem = os.path.splitext(os.path.basename(pdbPath))[0]
        parentSeq = Sequence(sequence=sequence, name=stem, id=stem,
                              description='DeepPTMPred input structure')

        outROIs = SetOfSequenceROIs(filename=self._getPath('sequenceROIs.sqlite'))
        for ptmType in PTM_TYPES:
            outCsv = self._getExtraPath(f'{ptmType}.csv')
            if not os.path.isfile(outCsv):
                continue
            threshold = CALIBRATED_THRESHOLDS.get(ptmType, DEFAULT_MIN_PROBABILITY)
            with open(outCsv, newline='') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    pos = int(row['position'])
                    residue = row['residue']
                    probability = float(row['probability'])
                    roiSeq = Sequence(sequence=residue, name=f'ROI_{pos}', id=f'ROI_{pos}',
                                       description=f'DeepPTMPred {ptmType} candidate')
                    seqROI = SequenceROI(sequence=parentSeq, seqROI=roiSeq, roiIdx=pos, roiIdx2=pos)
                    seqROI.setType(ptmType)
                    seqROI._scoreDeepptmpred = Float(probability)
                    seqROI._passesThreshold = Boolean(probability >= threshold)
                    seqROI._residueWt = String(residue)
                    seqROI._meanScore = Float(probability)
                    outROIs.append(seqROI)

        if len(outROIs) > 0:
            self._defineOutputs(outputROIs=outROIs)
            self._defineSourceRelation(self.inputStructure, outROIs)

    # ---------------------------------- Validation -------------------------------

    def _validate(self):
        return deepptmpredPlugin.validateInstallation()

    def _summary(self):
        summary = []
        if self.isFinished():
            outROIs = getattr(self, 'outputROIs', None)
            if outROIs is not None:
                nPass = sum(1 for roi in outROIs if roi._passesThreshold.get())
                summary.append(f'{nPass}/{len(outROIs)} candidate site(s) pass their calibrated threshold.')
        return summary
