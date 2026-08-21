=========
CHANGES
=========

0.5.0
=====
- PyRosetta is now auto-installed too (via the official
  ``pyrosetta-installer`` PyPI package, free for academic/non-commercial
  use, no account needed for this direct download) -- nothing manual
  remains for this plugin. The mirror this installer uses was previously
  found broken (2026-07-27: default 404, fallback TLS failure); re-tested
  for real 2026-08-21 in an isolated conda env and it now works
  end-to-end (~1.66GB wheel, real ``pyrosetta.init()`` run, version
  2026.33 dated 2026-08-13) -- the mirror's content/config evidently
  changed since. If it ever regresses, the manual fallback
  (``PYROSETTA_DOWNLOAD_URL``, requires a free academic account) is still
  documented.

0.4.1
=====
- Fixed a real upstream bug found via an actual end-to-end fresh conda
  env update on a Colab GPU session (Tesla T4, 2026-08-21): the real
  ``pred/train_PTM/environment.yml``'s own ``pip:`` block has
  ``tensorflow=2.15`` (single ``=``, invalid pip requirement syntax --
  real error: "= is not a valid operator. Did you mean == ?"). An
  earlier, undocumented edit had already patched a LOCAL clone of this
  repo elsewhere on this machine to ``==``, which is why this was missed
  until a genuinely fresh clone from GitHub was tested. Fixed with a
  ``sed`` patch on the filtered environment.yml before ``conda env
  update``. Verified after the fix: the full GPU branch (real
  ``cudatoolkit``/``cudnn``/torch install from the real file) completes
  successfully, with ``torch.cuda.is_available()`` and
  ``tf.config.list_physical_devices('GPU')`` both returning the real GPU.

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
