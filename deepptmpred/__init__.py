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
This package contains a protocol for PTM site prediction using a local
DeepPTMPred installation (structure-based, 17 PTM types).
"""

import os
import subprocess

from scipion.install.funcs import InstallHelper

from pwchem import Plugin as pwchemPlugin

from .constants import (
    DEEPPTMPRED_DIC, ESM_CONTACT_REGRESSION_FILENAME, ESM_CHECKPOINT_FILENAME,
    NOINSTALL_WARNING, PYROSETTA_DOWNLOAD_URL, UPSTREAM_URL,
)

_references = []  # DeepPTMPred does not have its own BibTeX entry yet (repo/README verified, no published bibtex).


class Plugin(pwchemPlugin):
    """DeepPTMPred (kuikui-wang/DeepPTMPred, CC BY-NC 4.0 -- see constants.py)
    is installed by cloning the upstream repo (it ships its own .h5 weights
    per PTM type) and building a dedicated conda environment (Python 3.10,
    TensorFlow 2.15, PyTorch 2.0, fair-esm -- see the repo's real
    environment.yml, ``pred/train_PTM/environment.yml``). TWO pieces remain
    manual: the ESM-2 checkpoint (2.6GB + its contact-regression companion)
    and PyRosetta (free academic license, wheel not redistributable nor
    reliably downloadable in this environment). The runner that invokes
    both libraries (``scripts/deepptmpred_runner.py``) is a maintained,
    byte-for-byte vendored copy (never rewritten from memory) of the
    original ``predict.py``, with 3 real scientific patches applied on top
    (see that file's docstring)."""

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(DEEPPTMPRED_DIC['home'], cls.getEnvName(DEEPPTMPRED_DIC))
        cls._defineVar(DEEPPTMPRED_DIC['activation'], cls.getEnvActivationCommand(DEEPPTMPRED_DIC))
        # Empty by default (same pattern as DEEPMVP_MODEL_DIR): the user
        # must point it to the ESM-2 checkpoint after the manual download.
        cls._defineVar(DEEPPTMPRED_DIC['esm_checkpoint'], '')

    @classmethod
    def defineBinaries(cls, env):
        cls.addDeepPTMPredPackage(env)

    @classmethod
    def addDeepPTMPredPackage(cls, env, default=True):
        home = cls.getVar(DEEPPTMPRED_DIC['home'])

        installer = InstallHelper(DEEPPTMPRED_DIC['name'], packageHome=home,
                                  packageVersion=DEEPPTMPRED_DIC['version'])

        # Clone BEFORE the conda environment (same rule as DeepMVP/NetCleave/
        # StackGlyEmbed -- see their __init__.py for the full explanation of
        # the problem this avoids).
        #
        # pythonVersion='3.10' (the repo's real environment.yml, 'python=3.10'
        # section). cudatoolkit/cudnn from the real environment.yml are NOT
        # installed here: the environment works 100% on CPU on a machine
        # with no GPU (TF 2.15 + torch 2.0 + fair-esm import and run without
        # CUDA), and forcing cudatoolkit=11.8 would fail the installation on
        # any machine without the corresponding NVIDIA drivers -- same
        # criterion already applied to StackGlyEmbed (explicit CPU-only
        # torch).
        #
        # pip installs: tensorflow==2.15/tensorflow-addons/fair-esm from the
        # real environment.yml, PLUS matplotlib/seaborn/scikit-learn/
        # imbalanced-learn/tqdm/joblib/logomaker: this repo's real conda
        # 'pip:' block does not ship these 7 even though 'predict.py'
        # imports them -- verified by running 'import predict' without them
        # (fails) and with them (works).
        installer.addCommand(
            f"git clone --depth 1 {UPSTREAM_URL} {home}",
            'DEEPPTMPRED_CLONED'
        ).getCondaEnvCommand(
            DEEPPTMPRED_DIC['name'], binaryVersion=DEEPPTMPRED_DIC['version'], pythonVersion='3.10'
        ).addCommand(
            f"{cls.getEnvActivationCommand(DEEPPTMPRED_DIC)} && "
            "pip install numpy scipy pandas h5py 'torch==2.0.*' biopython biotite "
            "'tensorflow==2.15' tensorflow-addons fair-esm 'scikit-learn>=1.6.1' "
            "'imbalanced-learn>=0.13.0' 'matplotlib>=3.10.3' 'seaborn>=0.13.2' "
            "'tqdm>=4.67.1' 'joblib>=1.4.2' 'logomaker>=0.8.7'",
            'DEEPPTMPRED_INSTALLED'
        ).addPackage(env, dependencies=['conda', 'git'], default=default)

    @classmethod
    def validateInstallation(cls):
        """Check that this plugin's requirements are met. Returns a list of
        actionable error messages, empty if the installation is correct."""
        errors = []

        trainPtmDir = cls.getTrainPtmDir()
        if not os.path.isdir(trainPtmDir) or not os.path.isfile(os.path.join(trainPtmDir, 'predict.py')):
            errors.append(f"Could not find 'predict.py' under '{trainPtmDir}' (DEEPPTMPRED_HOME/pred/train_PTM).")
        elif not cls.checkCallEnv(DEEPPTMPRED_DIC):
            errors.append("Activation of the DeepPTMPred conda environment failed.")

        esmCheckpoint = cls.getEsmCheckpointPath()
        if not esmCheckpoint or not os.path.isfile(esmCheckpoint):
            errors.append(
                f"DEEPPTMPRED_ESM_CHECKPOINT ('{esmCheckpoint}') not found -- download "
                f"'{ESM_CHECKPOINT_FILENAME}' manually (fair-esm's own weights, ~2.6GB)."
            )
        elif not os.path.isfile(os.path.join(os.path.dirname(esmCheckpoint), ESM_CONTACT_REGRESSION_FILENAME)):
            errors.append(
                f"'{ESM_CONTACT_REGRESSION_FILENAME}' (required companion file, must sit next to "
                f"DEEPPTMPRED_ESM_CHECKPOINT) not found in '{os.path.dirname(esmCheckpoint)}'."
            )

        if not errors and not cls.checkCallEnv(DEEPPTMPRED_DIC, extraImport='pyrosetta'):
            errors.append(
                f"PyRosetta is not installed in the DeepPTMPred conda environment -- academic-license "
                f"wheel, download manually from {PYROSETTA_DOWNLOAD_URL} and 'pip install <wheel>' "
                "inside the environment."
            )

        if errors:
            errors.append(NOINSTALL_WARNING)
        return errors

    @classmethod
    def checkCallEnv(cls, packageDic, extraImport=None):
        actCommand = cls.getVar(packageDic['activation'])
        importStatement = f'import tensorflow, torch, esm{"," + extraImport if extraImport else ""}'
        try:
            if 'conda' in actCommand and 'shell.bash hook' not in actCommand:
                actCommand = f'{cls.getCondaActivationCmd()}{actCommand}'
            subprocess.check_output(f'{actCommand} && python -c "{importStatement}"', shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    # ---------------------------------- Utils -----------------------------------

    @classmethod
    def getDeepPTMPredDir(cls):
        return cls.getVar(DEEPPTMPRED_DIC['home'])

    @classmethod
    def getTrainPtmDir(cls):
        return os.path.join(cls.getDeepPTMPredDir(), 'pred', 'train_PTM')

    @classmethod
    def getEsmCheckpointPath(cls):
        return cls.getVar(DEEPPTMPRED_DIC['esm_checkpoint'])

    @classmethod
    def getRunnerScriptPath(cls):
        # Vendorized inside THIS plugin (not the cloned repo) -- see
        # scripts/deepptmpred_runner.py.
        pluginDir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(pluginDir, 'scripts', 'deepptmpred_runner.py')

    # ---------------------------------- Protocol functions-----------------------

    @classmethod
    def runDeepPTMPred(cls, protocol, args, cwd=None):
        activation = cls.getVar(DEEPPTMPRED_DIC['activation'])
        scriptPath = cls.getRunnerScriptPath()
        # MPLBACKEND=Agg: 'predict.py' imports matplotlib.pyplot and would
        # inherit an interactive/inline backend from the parent process
        # that does not exist in the isolated conda environment.
        fullProgram = f'MPLBACKEND=Agg {activation} && python {scriptPath}'
        protocol.runJob(fullProgram, args, env=cls.getEnviron(), cwd=cwd)
