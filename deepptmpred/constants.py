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

UPSTREAM_URL = 'https://github.com/kuikui-wang/DeepPTMPred'

# Confirmed by reading the vendorized runner (scripts/deepptmpred_runner.py::
# _extract_esm_features, line ~101): 'torch.device("cuda" if
# torch.cuda.is_available() else "cpu")' -- decided IN CODE, with no CLI
# flag to expose (unlike TMbed/DiscoTope-3.0, which do expose a real GPU
# flag). The protocol's USE_GPU/GPU_LIST hidden params act on that
# decision indirectly, via CUDA_VISIBLE_DEVICES (see runDeepPTMPred in
# __init__.py), same criterion applied to DeepMVP/EMNGly/MeToken.
GPU_REQUIRED = True

# DeepPTMPred license (upstream): the repo does not declare its own LICENSE;
# the source code is subject to the same terms as the paper, CC BY-NC 4.0
# (Oxford University Press) -- non-commercial use only.
LICENSE_NOTE = 'CC BY-NC 4.0 -- non-commercial use only.'

# Weights ARE included in the cloned repo (.h5 per PTM type, ~19MB each) --
# unlike DeepMVP, there is no separate model download.
#
# The ESM-2 checkpoint (esm2_t33_650M_UR50D.pt, 2.6GB) is now auto-downloaded
# at install time into '<DEEPPTMPRED_HOME>/checkpoints/' (see
# addDeepPTMPredPackage in __init__.py). It must be accompanied by
# 'esm2_t33_650M_UR50D-contact-regression.pt' (required companion file, see
# the docstring of 'scripts/deepptmpred_runner.py::_extract_esm_features')
# in the SAME directory -- also auto-downloaded.
# Re-verified via 'curl -sIL' on both URLs (real 200, correct
# content-length, served via CloudFront/S3) after this download was once
# found unreliable inside a real 'scipion3 installb' run -- '--retry 3'
# added to the install command below as a hedge against that
# previously-observed flakiness recurring, rather than assuming success
# makes it permanently reliable.
ESM_CHECKPOINT_FILENAME = 'esm2_t33_650M_UR50D.pt'
ESM_CONTACT_REGRESSION_FILENAME = 'esm2_t33_650M_UR50D-contact-regression.pt'
ESM_DOWNLOAD_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt'
)
ESM_CONTACT_REGRESSION_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/regression/'
    'esm2_t33_650M_UR50D-contact-regression.pt'
)

# PyRosetta: free for academic/non-commercial use (RosettaCommons).
# Auto-installed at install time via the official 'pyrosetta-installer'
# PyPI package (anonymous direct download from RosettaCommons' own mirror,
# no account/login needed -- distinct from the manual browser download at
# https://www.pyrosetta.org/downloads, which DOES require a free academic
# account, but that page is only for humans; the installer hits the same
# mirror directly). This download was once found broken (default mirror
# 404, fallback failing TLS verification) -- re-tested for real since and
# both the download and 'pyrosetta.init()' now work end-to-end (real
# wheel, ~1.66GB) -- the mirror's content/config has evidently changed.
# If this ever regresses again, PYROSETTA_DOWNLOAD_URL below is the
# manual fallback (requires the free academic account).
PYROSETTA_DOWNLOAD_URL = 'https://www.pyrosetta.org/downloads'

# 17 PTM types predicted by DeepPTMPred (one .h5 model per type, one runner
# invocation per type) -- matches the runner's own 'choices' list (see
# 'scripts/deepptmpred_runner.py').
PTM_TYPES = (
    'phosphorylation', 'acetylation', 'ubiquitination', 'hydroxylation',
    'gamma_carboxyglutamic_acid', 'lys_methylation', 'malonylation',
    'arg_methylation', 'crotonylation', 'succinylation', 'glutathionylation',
    'sumoylation', 's_nitrosylation', 'glutarylation', 'citrullination',
    'o_linked_glycosylation', 'n_linked_glycosylation',
)

# Per-type calibrated thresholds, empirically derived per PTM type rather
# than using DeepPTMPred's own uniform 0.5 cutoff. Generic 0.5 fallback if
# a future type has no calibration of its own.
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
