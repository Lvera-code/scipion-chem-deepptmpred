================================
DeepPTMPred Scipion plugin
================================

Scipion framework plugin wrapping DeepPTMPred (Briefings in Bioinformatics) --
second consensus engine (PDB path only, 17 PTM types, requires PyRosetta for
per-residue SASA).

``ProtDeepPTMPredPrediction`` invokes a vendorized runner, a maintained
byte-for-byte copy of the upstream ``predict.py`` with 3 real scientific
patches applied -- see ``deepptmpred/scripts/deepptmpred_runner.py``.

Original repo: https://github.com/kuikui-wang/DeepPTMPred

Citation: doi.org/10.1093/bib/bbag321

**DeepPTMPred license (upstream)**: the original repo does not declare its
own LICENSE; the paper is CC BY-NC 4.0 (Oxford University Press) and the
source code has been confirmed to be under the same terms -- non-commercial
use is covered without issue.

===================
Install this plugin
===================

**Developer's version**

.. code-block::

            git clone https://github.com/Lvera-code/scipion-chem-deepptmpred.git
            cd scipion-chem-deepptmpred
            scipion3 installp -p . --devel
            scipion3 installb DeepPTMPred

The repo (including its .h5 weights), the conda environment (Python 3.10,
TensorFlow 2.15, PyTorch 2.0, fair-esm -- installed from the repo's own
``pred/train_PTM/environment.yml``), the ESM-2 checkpoint
(``esm2_t33_650M_UR50D.pt``, ~2.6GB, + its required companion file
``esm2_t33_650M_UR50D-contact-regression.pt``) AND PyRosetta (free for
academic/non-commercial use, via the official ``pyrosetta-installer`` PyPI
package) are all installed automatically -- nothing manual remains. Only
set ``DEEPPTMPRED_ESM_CHECKPOINT`` in ``scipion.conf`` if you want to point
at a different checkpoint instead.

.. code-block::

            scipion3 tests deepptmpred.tests
