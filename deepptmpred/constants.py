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

DEFAULT_VERSION = '1.0'

DEEPPTMPRED_DIC = {
    'name': 'DeepPTMPred',
    'version': DEFAULT_VERSION,
    'home': 'DEEPPTMPRED_HOME',
    'activation': 'DEEPPTMPRED_ACTIVATION_CMD',
    'esm_checkpoint': 'DEEPPTMPRED_ESM_CHECKPOINT',
}

READ_URL = 'https://github.com/Lvera-code/scipion-chem-deepptmpred'
UPSTREAM_URL = 'https://github.com/kuikui-wang/DeepPTMPred'

# Confirmed by reading the vendorized runner (scripts/deepptmpred_runner.py::
# _extract_esm_features, line ~101): 'torch.device("cuda" if
# torch.cuda.is_available() else "cpu")' -- decided IN CODE, with no CLI
# flag to expose (unlike TMbed/DiscoTope-3.0, the only 2 plugins in project 1
# with a real GPU flag). No useGPU parameter is added to the protocol (same
# criterion applied to DeepMVP).
GPU_REQUIRED = True

# DeepPTMPred license (upstream): the repo does not declare its own LICENSE;
# the source code is subject to the same terms as the paper, CC BY-NC 4.0
# (Oxford University Press) -- non-commercial use only. See
# PTM-Prediction/STATUS.md for the verification details.
LICENSE_NOTE = 'CC BY-NC 4.0 -- non-commercial use only.'

# Weights ARE included in the cloned repo (.h5 per PTM type, ~19MB each,
# confirmed in the PTM-Prediction/src/engines/deepptmpred_engine.py
# docstring) -- unlike DeepMVP, there is no separate model download.
#
# The ESM-2 checkpoint (esm2_t33_650M_UR50D.pt, 2.6GB) IS manual: although
# 'fair-esm' normally allows downloading it via its own code
# (dl.fbaipublicfiles.com), PTM-Prediction/STATUS.md (line ~185) records
# that it was installed manually in this same organization -- the same
# pattern is kept here rather than automating a download never before
# verified in a real 'scipion3 installb' run. It must be accompanied by
# 'esm2_t33_650M_UR50D-contact-regression.pt' (required companion file, see
# the docstring of 'scripts/deepptmpred_runner.py::_extract_esm_features')
# in the SAME directory.
ESM_CHECKPOINT_FILENAME = 'esm2_t33_650M_UR50D.pt'
ESM_CONTACT_REGRESSION_FILENAME = 'esm2_t33_650M_UR50D-contact-regression.pt'
ESM_DOWNLOAD_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt'
)
ESM_CONTACT_REGRESSION_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/regression/'
    'esm2_t33_650M_UR50D-contact-regression.pt'
)

# PyRosetta: free academic license (RosettaCommons), wheel NOT
# redistributable and not reliably downloadable in this environment
# (STATUS.md line ~194-205: the installer's default mirrors failed, really
# and reproducibly -- 404/TLS -- on this machine). 100% manual installation,
# same pattern as NETMHCPAN_HOME in project 1: the user downloads the
# wheel themselves (https://www.pyrosetta.org/downloads, requires a free
# academic account) and installs it with 'pip install <wheel>' INSIDE this
# plugin's conda environment.
PYROSETTA_DOWNLOAD_URL = 'https://www.pyrosetta.org/downloads'

# 17 PTM types predicted by DeepPTMPred (one .h5 model per type, one runner
# invocation per type) -- verified against
# PTM-Prediction/src/config/settings.py::DEEPPTMPRED_PTM_TYPES, which in
# turn cites the runner's real 'choices' list (line ~237-243).
PTM_TYPES = (
    'phosphorylation', 'acetylation', 'ubiquitination', 'hydroxylation',
    'gamma_carboxyglutamic_acid', 'lys_methylation', 'malonylation',
    'arg_methylation', 'crotonylation', 'succinylation', 'glutathionylation',
    'sumoylation', 's_nitrosylation', 'glutarylation', 'citrullination',
    'o_linked_glycosylation', 'n_linked_glycosylation',
)

# Per-type calibrated thresholds (verified against
# PTM-Prediction/src/config/settings.py::DEEPPTMPRED_CALIBRATED_THRESHOLDS,
# already validated end-to-end in the standalone pipeline -- see STATUS.md
# "Real DeepPTMPred calibration"). Generic 0.5 fallback if a future type
# has no calibration of its own.
CALIBRATED_THRESHOLDS = {
    'acetylation': 0.6350621,
    'arg_methylation': 0.34068727,
    'citrullination': 0.36854228,
    'crotonylation': 0.86312497,
    'gamma_carboxyglutamic_acid': 0.24807824,
    'glutarylation': 0.4747097,
    'glutathionylation': 0.466462,
    'hydroxylation': 0.35899624,
    'lys_methylation': 0.43064716,
    'malonylation': 0.41699925,
    'n_linked_glycosylation': 0.99802846,
    'o_linked_glycosylation': 0.2619363,
    'phosphorylation': 0.24020174,
    's_nitrosylation': 0.5140331,
    'succinylation': 0.50403893,
    'sumoylation': 0.37326753,
    'ubiquitination': 0.5321394,
}
DEFAULT_MIN_PROBABILITY = 0.5

NOINSTALL_WARNING = (
    "DeepPTMPred is not installed correctly. Check that the repo has been cloned "
    "(DEEPPTMPRED_HOME), that the ESM-2 checkpoint (together with its companion "
    "'-contact-regression.pt' file) is at DEEPPTMPRED_ESM_CHECKPOINT, and that PyRosetta is "
    "installed in the plugin's conda environment (manual download, free academic account "
    f"at {PYROSETTA_DOWNLOAD_URL}). See README.rst - Installation."
)
