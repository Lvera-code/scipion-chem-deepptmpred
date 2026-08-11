=========
CHANGES
=========

0.2.0
=====
- Real protocol (``ProtDeepPTMPredPrediction``): single-chain structure ->
  candidate PTM sites (17 types, one ``SequenceROI`` per site,
  ``_type``/``_scoreDeepptmpred``/``_passesThreshold`` with a per-type
  calibrated threshold/``_meanScore``). Runner vendorized byte-for-byte from
  the standalone project (3 real scientific patches preserved). Automatic
  installation of the repo+conda environment; ESM-2 checkpoint and
  PyRosetta remain manual (documented with the real reason). Real test on
  7c4s (same fixture and mmCIF label/auth chain gotcha already resolved in
  scipion-chem-discotope).

0.1.0
=====
- Initial scaffolding: Scipion plugin structure generated following the
  same pattern as the BCell-Epitope-Prediction plugins (one plugin per
  tool). No installation or protocol logic yet -- pending end-to-end
  validation of the pipeline on Colab, see the ``PTM-Prediction`` project's
  STATUS.md.
