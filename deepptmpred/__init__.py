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

_references = []  # DeepPTMPred no tiene una entrada BibTeX propia todavia (repo/README verificados, sin bibtex propio publicado).


class Plugin(pwchemPlugin):
    """DeepPTMPred (kuikui-wang/DeepPTMPred, CC BY-NC 4.0 -- ver constants.py)
    se instala clonando el repo upstream (trae sus propios pesos .h5 por
    tipo de PTM) y construyendo un entorno conda dedicado (Python 3.10,
    TensorFlow 2.15, PyTorch 2.0, fair-esm -- ver environment.yml real del
    repo, ``pred/train_PTM/environment.yml``). DOS piezas quedan
    manuales: el checkpoint ESM-2 (2.6GB + companero de regresion de
    contactos) y PyRosetta (licencia academica gratuita, wheel no
    redistribuible ni descargable de forma fiable en este entorno -- ver
    STATUS.md del proyecto hermano). El runner que invoca ambas librerias
    (``scripts/deepptmpred_runner.py``) esta VENDORIZADO byte-a-byte desde
    el proyecto standalone, con 3 parches cientificos reales ya aplicados
    (ver docstring de ese archivo) -- nunca se reescribe de memoria."""

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(DEEPPTMPRED_DIC['home'], cls.getEnvName(DEEPPTMPRED_DIC))
        cls._defineVar(DEEPPTMPRED_DIC['activation'], cls.getEnvActivationCommand(DEEPPTMPRED_DIC))
        # Vacio por defecto (mismo patron que DEEPMVP_MODEL_DIR): el
        # usuario debe apuntarlo al checkpoint ESM-2 tras la descarga
        # manual.
        cls._defineVar(DEEPPTMPRED_DIC['esm_checkpoint'], '')

    @classmethod
    def defineBinaries(cls, env):
        cls.addDeepPTMPredPackage(env)

    @classmethod
    def addDeepPTMPredPackage(cls, env, default=True):
        home = cls.getVar(DEEPPTMPRED_DIC['home'])

        installer = InstallHelper(DEEPPTMPRED_DIC['name'], packageHome=home,
                                  packageVersion=DEEPPTMPRED_DIC['version'])

        # Clone ANTES del entorno conda (misma regla que DeepMVP/NetCleave/
        # StackGlyEmbed -- ver sus __init__.py para la explicacion completa
        # del problema que esto evita).
        #
        # pythonVersion='3.10' (environment.yml real del repo, seccion
        # 'python=3.10'). cudatoolkit/cudnn del environment.yml real NO se
        # instalan aqui: verificado en PTM-Prediction/STATUS.md que el
        # entorno funciona 100% en CPU en una maquina sin GPU (TF 2.15 +
        # torch 2.0 + fair-esm importan y ejecutan sin CUDA), y forzar
        # cudatoolkit=11.8 fallaria la instalacion en cualquier maquina sin
        # los drivers NVIDIA correspondientes -- mismo criterio ya aplicado
        # a StackGlyEmbed (torch CPU-only explicito).
        #
        # pip installs: tensorflow==2.15/tensorflow-addons/fair-esm del
        # environment.yml real, MAS matplotlib/seaborn/scikit-learn/
        # imbalanced-learn/tqdm/joblib/logomaker -- verificado en
        # STATUS.md ("Dependencias de environment.yml incompletas en el
        # conda env real") que el conda 'pip:' block real de este repo NO
        # trae estas 7 pese a que 'predict.py' las importa; verificado
        # ejecutando 'import predict' sin ellas (falla) y con ellas
        # (funciona).
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
        # Vendorizado dentro de ESTE plugin (no del repo clonado) -- ver
        # scripts/deepptmpred_runner.py.
        pluginDir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(pluginDir, 'scripts', 'deepptmpred_runner.py')

    # ---------------------------------- Protocol functions-----------------------

    @classmethod
    def runDeepPTMPred(cls, protocol, args, cwd=None):
        activation = cls.getVar(DEEPPTMPRED_DIC['activation'])
        scriptPath = cls.getRunnerScriptPath()
        # MPLBACKEND=Agg (mismo motivo real documentado en
        # PTM-Prediction/src/engines/deepptmpred_engine.py): 'predict.py'
        # importa matplotlib.pyplot y hereda un backend interactivo/inline
        # del proceso padre que no existe en el entorno conda aislado.
        fullProgram = f'MPLBACKEND=Agg {activation} && python {scriptPath}'
        protocol.runJob(fullProgram, args, env=cls.getEnviron(), cwd=cwd)
