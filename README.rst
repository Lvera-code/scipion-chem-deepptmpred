================================
DeepPTMPred Scipion plugin
================================

Scipion framework plugin wrapping DeepPTMPred (Briefings in Bioinformatics) --
second consensus engine (PDB path only, 17 PTM types, requires PyRosetta for
per-residue SASA).

``ProtDeepPTMPredPrediction`` invokes a vendorized runner (identical to the
one already validated end-to-end in the standalone pipeline, with 3
scientific patches applied -- see ``deepptmpred/scripts/deepptmpred_runner.py``).

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

The repo (including its .h5 weights) and the conda environment (Python 3.10,
TensorFlow 2.15, PyTorch 2.0, fair-esm) are installed automatically. TWO
pieces remain **manual**:

- ESM-2 checkpoint (``esm2_t33_650M_UR50D.pt``, ~2.6GB) + its required
  companion file (``esm2_t33_650M_UR50D-contact-regression.pt``) in the SAME
  directory -- point ``DEEPPTMPRED_ESM_CHECKPOINT`` (in ``scipion.conf``) to
  the former.
- PyRosetta (free academic license, account at
  https://www.pyrosetta.org/downloads) -- download the wheel and
  ``pip install <wheel>`` INSIDE the conda environment
  (``conda activate DeepPTMPred-1.0``).

.. code-block::

            scipion3 tests deepptmpred.tests
