=========
CHANGES
=========

0.4.0
=====
- GPU support: ``USE_GPU``/``GPU_LIST`` hidden params added to
  ``ProtDeepPTMPredPrediction``, wired to ``CUDA_VISIBLE_DEVICES`` in
  ``runDeepPTMPred`` (the runner decides GPU/CPU itself via
  ``torch.cuda.is_available()``, no native CLI flag -- this is the real
  lever on that decision). Install now keeps the real ``cudatoolkit``/
  ``cudnn`` conda entries and installs the default (CUDA-capable) torch
  wheel when a GPU is detected; without one (this dev machine's case, the
  only branch verified here) stays exactly the already-verified
  CPU-only-wheel behavior. The ``CUDA_VISIBLE_DEVICES`` lever itself was
  verified for real against torch on a Colab GPU session (Tesla T4):
  ``torch.cuda.is_available()`` flips False/True exactly as expected.

0.3.0
=====
- Installed from the repo's own real ``environment.yml`` (via
  ``conda env update -f``, GPU-only conda entries filtered out) instead of
  a hand-reconstructed package list. ESM-2 checkpoint (+ contact-regression
  companion) now auto-downloaded at install time into
  ``<DEEPPTMPRED_HOME>/checkpoints/`` -- only PyRosetta remains manual.
  Removed unused ``READ_URL`` constant.

0.2.0
=====
- Real protocol (``ProtDeepPTMPredPrediction``): single-chain structure ->
  candidate PTM sites (17 types, one ``SequenceROI`` per site,
  ``_type``/``_scoreDeepptmpred``/``_passesThreshold`` with a per-type
  calibrated threshold/``_meanScore``). Runner vendorized byte-for-byte from
  the upstream ``predict.py`` (3 real scientific patches preserved). Automatic
  installation of the repo+conda environment; ESM-2 checkpoint and
  PyRosetta remain manual (documented with the real reason). Real test on
  7c4s (same fixture and mmCIF label/auth chain gotcha already resolved in
  scipion-chem-discotope).

0.1.0
=====
- Initial scaffolding: Scipion plugin structure generated following the
  same one-plugin-per-tool pattern used across this project's other
  plugins. No installation or protocol logic yet.
