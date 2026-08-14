=========
CHANGES
=========

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
