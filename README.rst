================================
DeepPTMPred Scipion plugin
================================

Scipion framework plugin wrapping DeepPTMPred (Briefings in Bioinformatics) --
segundo motor de consenso (Camino PDB unicamente, 17 tipos de PTM, requiere PyRosetta para SASA por residuo).

**Estado: protocolo real implementado, pendiente de instalacion+test real**
(ver ``PTM-Prediction/STATUS.md``, entrada 2026-08-11 -- el gate de Carlos
para empezar la migracion a Scipion ya esta cerrado). ``ProtDeepPTMPredPrediction``
invoca un runner vendorizado (identico al ya validado end-to-end en el
pipeline standalone, con 3 parches cientificos reales aplicados -- ver
``deepptmpred/scripts/deepptmpred_runner.py``).

Repo original: https://github.com/kuikui-wang/DeepPTMPred

Cita: doi.org/10.1093/bib/bbag321

**Licencia de DeepPTMPred (upstream)**: el repo original no declara LICENSE propia, pero el paper es CC BY-NC 4.0 (Oxford University Press) y Junwen Wang (autor de correspondencia) confirmo por email el 2026-07-29 que el codigo sigue los mismos terminos -- uso no comercial (TFG/CNB-CSIC) cubierto sin problema.

===================
Install this plugin
===================

**Developer's version**

.. code-block::

            git clone https://github.com/Lvera-code/scipion-chem-deepptmpred.git
            cd scipion-chem-deepptmpred
            scipion3 installp -p . --devel
            scipion3 installb DeepPTMPred

El repo (con sus pesos .h5 incluidos) y el entorno conda (Python 3.10,
TensorFlow 2.15, PyTorch 2.0, fair-esm) se instalan automaticamente. DOS
piezas quedan **manuales**:

- Checkpoint ESM-2 (``esm2_t33_650M_UR50D.pt``, ~2.6GB) + su companero
  obligatorio (``esm2_t33_650M_UR50D-contact-regression.pt``) en el MISMO
  directorio -- apunta ``DEEPPTMPRED_ESM_CHECKPOINT`` (en ``scipion.conf``)
  al primero.
- PyRosetta (licencia academica gratuita, cuenta en
  https://www.pyrosetta.org/downloads) -- descarga el wheel y
  ``pip install <wheel>`` DENTRO del entorno conda
  (``conda activate DeepPTMPred-1.0``).

.. code-block::

            scipion3 tests deepptmpred.tests
