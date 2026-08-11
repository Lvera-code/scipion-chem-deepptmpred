=========
CHANGES
=========

0.2.0
=====
- Protocolo real (``ProtDeepPTMPredPrediction``): estructura de cadena unica
  -> sitios PTM candidatos (17 tipos, un ``SequenceROI`` por sitio,
  ``_type``/``_scoreDeepptmpred``/``_passesThreshold`` con umbral calibrado
  por tipo/``_meanScore``). Runner vendorizado byte-a-byte desde el proyecto
  standalone (3 parches cientificos reales preservados). Instalacion
  automatica del repo+entorno conda; checkpoint ESM-2 y PyRosetta manuales
  (documentados con motivo real). Test real sobre 7c4s (mismo fixture y
  gotcha mmCIF label/auth chain ya resuelto en scipion-chem-discotope).

0.1.0
=====
- Scaffolding inicial: estructura de plugin de Scipion generada siguiendo el
  mismo patron que los plugins de BCell-Epitope-Prediction (un plugin por
  herramienta). Sin logica de instalacion ni de protocolo todavia -- pendiente
  de la validacion end-to-end del pipeline en Colab, ver STATUS.md del
  proyecto ``PTM-Prediction``.
