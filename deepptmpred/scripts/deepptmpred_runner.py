#!/usr/bin/env python
"""Standalone runner for DeepPTMPred (Phase 2, engine 2/2 of the PDB-path consensus).

VENDORIZED byte-for-byte from
``PTM-Prediction/src/engines/_deepptmpred_runner.py`` -- this file is NEVER
edited to "port" its logic: the 3 scientific patches it contains (Keras
Lambda/K deserialization, phi/psi forced to 0.0 to match the training
distribution, plDDT re-indexing via the real CA atom) were empirically
verified against the paper's published AUROC (see the docstrings of
``_load_predict_module``/``_patched_calculate_features`` below) --
reimplementing them from memory would risk losing that verification. Any
change to the prediction logic must be made in the sibling
``PTM-Prediction`` project first and synced here afterward, same criterion
as ``predict_local.py`` in ``scipion-chem-stackglyembed``.

This script NEVER imports PTM-Prediction's ``src`` package -- it requires
torch/tensorflow/tensorflow-addons/pyrosetta/fair-esm, dependencies ONLY
present in this plugin's dedicated conda environment
(``DEEPPTMPRED_ACTIVATION_CMD``). It is invoked EXCLUSIVELY via subprocess
from ``ProtDeepPTMPredPrediction`` (``protocols/protocol_deepptmpred.py``).

Why this runner exists instead of invoking the repo's scripts directly
(unlike DeepMVP, which does have a real CLI): the source code at
github.com/kuikui-wang/DeepPTMPred shows that neither ``predict.py`` nor
``e2_single_data.py`` has a CLI -- both hardcode ``ptm_type``/``pdb_path``/
``protein_id``/the ESM checkpoint path inside their
``if __name__ == "__main__":`` block. This runner imports the two classes
that ARE correctly parametrized from ``predict.py`` (``PredictConfig``,
``PTMPredictor``, both receive their arguments via constructor) and
REIMPLEMENTS ESM-2 feature extraction instead of calling
``e2_single_data.py::extract_full_sequence_esm``: that function redefines
``custom_checkpoint_path`` as a LOCAL variable with a hardcoded absolute
AutoDL path (``/root/autodl-tmp/...``), ignoring any value passed as a
parameter or from the module.

It also avoids ``predict.py::extract_protein_id_from_pdb_path`` /
``extract_sequence_from_pdb`` (which require an AlphaFold-style filename,
e.g. ``AF-P12345-F1-model_v4.pdb``, and perform their own ATMSEQ
extraction redundant with ``src.utils.structure_parser``): this runner
receives the accession and sequence already sanitized by Phase 1.5 as
explicit arguments, guaranteeing that DeepMVP and DeepPTMPred report
exactly the same position numbering for the same accession.
"""

import argparse
import contextlib
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Output columns: 'probability' is DeepPTMPred's raw score (always kept);
# the repo's own 'prediction' column (hardcoded 0.5 cutoff, not calibrated
# against any validation set) is deliberately discarded -- the real filter
# is applied by the Phase 3 core, not this runner.
OUTPUT_COLUMNS = ["protein_id", "position", "residue", "probability", "ptm_type"]


def _esm_cache_path(custom_esm_dir: Path, protein_id: str, sequence: str) -> Path:
    """ESM feature cache filename, hashed against the real sequence.

    A cache key based only on ``protein_id``
    (``{protein_id}_full_esm.npz``) would silently reuse the old ESM
    embedding when re-running the pipeline with a DIFFERENT sequence under
    the same accession (e.g. an updated PDB with the same filename),
    predicting on the wrong sequence with no error or warning. The hash
    (sha256, first 12 hex characters, enough to avoid accidental
    collisions without making the filename too long) makes a different
    sequence ALWAYS a different cache -- there is no need to read/compare
    the existing .npz to decide whether to reuse it.
    """
    sequence_hash = hashlib.sha256(sequence.encode("utf-8")).hexdigest()[:12]
    return custom_esm_dir / f"{protein_id}_{sequence_hash}_full_esm.npz"


def _extract_esm_features(sequence: str, checkpoint_path: Path, esm_dim: int = 1280) -> np.ndarray:
    """Own reimplementation of e2_single_data.py::extract_full_sequence_esm.

    Same logic (chunking to 1022 tokens, representation layer 33, CLS/SEP
    discarded), but ``checkpoint_path`` IS honored -- the original ignores
    it (see the module docstring).

    100% local: reading ``esm/pretrained.py`` directly from
    github.com/facebookresearch/esm confirms that
    ``pretrained.load_model_and_alphabet(model_name)`` does
    ``if model_name.endswith(".pt"): return load_model_and_alphabet_local(...)``
    -- since ``checkpoint_path`` is always a local ``.pt`` path (never a
    model name like ``"esm2_t33_650M_UR50D"``), it ALWAYS takes the local
    branch, which only uses ``torch.load()`` on files on disk. The branch
    that does download over the network (``load_model_and_alphabet_hub``,
    against ``dl.fbaipublicfiles.com``) is never reached.

    Real detail (not a network issue, but a file one): the local branch
    also tries to load a COMPANION file
    ``<checkpoint>-contact-regression.pt`` in the same directory (fair-esm's
    internal heuristic, ``_has_regression_weights``, does not exclude
    ``esm2_*`` models). If missing, it fails with a LOCAL
    ``FileNotFoundError`` when attempting ``torch.load()`` on that file --
    make sure this companion file is also downloaded alongside the main
    checkpoint (see ``Settings.DEEPPTMPRED_ESM_CHECKPOINT``).
    """
    import torch
    from esm import pretrained

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # safe_globals arrived in torch 2.4 (weights_only=True became the
    # default in 2.6) -- DeepPTMPred's environment.yml pins pytorch=2.0,
    # which neither has the attribute nor needs it (its default
    # torch.load is already weights_only=False, allowing the unpickle of
    # argparse.Namespace without further action).
    safe_ctx = (
        torch.serialization.safe_globals([argparse.Namespace])
        if hasattr(torch.serialization, "safe_globals")
        else contextlib.nullcontext()
    )
    with safe_ctx:
        model, alphabet = pretrained.load_model_and_alphabet(str(checkpoint_path))
    model = model.to(device)
    model.eval()
    batch_converter = alphabet.get_batch_converter()

    max_len = 1022  # leave room for CLS/SEP tokens (ESM-2's real limit)
    chunks = [sequence[i : i + max_len] for i in range(0, len(sequence), max_len)]
    full_features = np.zeros((len(sequence), esm_dim))

    for i, chunk in enumerate(chunks):
        data = [(f"chunk{i}", chunk)]
        _, _, tokens = batch_converter(data)
        tokens = tokens.to(device)
        with torch.no_grad():
            results = model(tokens, repr_layers=[33])
            features = results["representations"][33][0, 1:-1].cpu().numpy()
        start = i * max_len
        end = start + len(chunk)
        full_features[start:end] = features[: len(chunk)]

    return full_features


def _load_predict_module(train_ptm_dir: Path):
    """Inserts ``train_ptm_dir`` into sys.path and imports the repo's ``predict`` module.

    Deferred import (inside the function, not at module level): the heavy
    dependencies of ``predict.py`` (tensorflow, pyrosetta,
    tensorflow_addons) must only load when the runner actually executes,
    never when this file is parsed.

    Also patches ``predict.load_model`` here: the saved model has a
    ``Lambda`` layer (``model.py::182``,
    ``Lambda(lambda xin: K.sum(xin, axis=1))``) whose serialized function
    references the symbol ``K`` (alias for ``tensorflow.keras.backend``)
    at reconstruction time -- Keras ONLY resolves those symbols via the
    ``custom_objects`` dict passed to ``load_model``, never via the
    globals of the module importing it (even though ``predict.py`` does
    have ``K`` in its own namespace). The real ``custom_objects`` in
    ``PTMPredictor.__init__`` does not include ``'K'``, so loading any
    model fails with ``NameError: name 'K' is not defined``. Verified by
    running the phosphorylation model without the patch (fails) and with
    the patch (loads correctly). ``predict.py`` is not edited (vendored,
    same criterion as the rest of the runner): the function is wrapped on
    the already-imported module.
    """
    sys.path.insert(0, str(train_ptm_dir))
    import predict

    _original_load_model = predict.load_model

    def _patched_load_model(*args, **kwargs):
        custom_objects = dict(kwargs.get("custom_objects") or {})
        custom_objects.setdefault("K", predict.K)
        kwargs["custom_objects"] = custom_objects
        return _original_load_model(*args, **kwargs)

    predict.load_model = _patched_load_model

    # Patch 2: train/inference distribution mismatch --
    # ``data_loader.py::L139-141`` (the paper's training AND evaluation
    # pipeline) computes ``phi_center``/``psi_center`` with
    # ``half_window = (max(window_sizes)-1)//2 = 25``, but the source
    # CSV's phi/psi array only has 11 elements -- the condition
    # ``len(x) > half_window`` is ALWAYS false, so the shipped model never
    # saw anything other than 0.0 in those two angles, neither in training
    # nor in the test set that produces the AUCs published in the paper.
    # But ``PyRosettaCalculator.calculate_features`` (real inference, the
    # one this runner uses) DOES compute real phi/psi via PyRosetta --
    # that takes the model out of its training distribution. Empirically
    # verified (calibration script, n=75): forcing phi=psi=0.0 at
    # inference raises the real hydroxylation AUROC from 0.342 to 0.934
    # (paper: 0.965) and lys_methylation's from 0.462 to 0.883 (paper:
    # 0.899) -- recovers the published performance. This matches inference
    # to what the model actually learned, it is not a features
    # improvement: the model does not know how to use real phi/psi.
    _original_calculate_features = predict.PyRosettaCalculator.calculate_features

    # Patch 3: indexing bug (see STATUS.md,
    # "n_linked_glycosylation and the 4 mediocre types investigation").
    # ``PyRosettaCalculator.__init__`` builds
    # ``self.plDDT_values`` by iterating PER ATOM
    # (``[atom.get_bfactor() for atom in structure.get_atoms()]``, ~L260),
    # but ``calculate_features`` indexes it PER RESIDUE NUMBER
    # (``self.plDDT_values[residue_number - 1]``, ~L300) -- with ~7
    # atoms/residue in an AlphaFold PDB, residue N's "local_plDDT" ends up
    # actually being the B-factor of an atom from a completely different
    # residue (~N/7). Empirically verified: correlation against the real
    # CA B-factor = 0.031; with this fix = 0.927. Real AUROC measured
    # after the fix: citrullination 0.657->0.778 (matches the paper
    # exactly), s_nitrosylation 0.683->0.770. ``predict.py`` is not
    # touched (vendored): ``local_plDDT`` is recomputed directly from
    # ``self.pose`` (the same PDB already loaded by PyRosetta), taking the
    # real B-factor of the requested residue's CA atom -- it does not
    # depend at all on the mis-indexed ``self.plDDT_values`` array.
    def _patched_calculate_features(self, residue_number):
        feat = _original_calculate_features(self, residue_number)
        feat = feat.copy()
        feat[1] = 0.0  # phi
        feat[2] = 0.0  # psi
        try:
            ca_atom_index = self.pose.residue(residue_number).atom_index("CA")
            feat[6] = self.pose.pdb_info().bfactor(residue_number, ca_atom_index)  # local_plDDT
        except Exception:
            pass  # leave the (mis-indexed) local_plDDT already carried by the original array
        return feat

    predict.PyRosettaCalculator.calculate_features = _patched_calculate_features

    return predict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Standalone DeepPTMPred runner (one PTM type per invocation)."
    )
    parser.add_argument("--train-ptm-dir", required=True, help="Path to DeepPTMPred/pred/train_PTM")
    parser.add_argument("--protein-id", required=True)
    parser.add_argument("--sequence", required=True, help="ATMSEQ sequence already sanitized by Phase 1.5")
    parser.add_argument("--pdb-path", required=True, help="Single-chain PDB (Phase 1.5)")
    # List deliberately duplicated from Settings.DEEPPTMPRED_PTM_TYPES: this
    # script runs in DeepPTMPred's dedicated venv, it never imports 'src'
    # (see the module docstring). If the repo adds/removes a PTM type,
    # update both lists (here and in src/config/settings.py).
    parser.add_argument("--ptm-type", required=True, choices=[
        "phosphorylation", "acetylation", "ubiquitination", "hydroxylation",
        "gamma_carboxyglutamic_acid", "lys_methylation", "malonylation",
        "arg_methylation", "crotonylation", "succinylation", "glutathionylation",
        "sumoylation", "s_nitrosylation", "glutarylation", "citrullination",
        "o_linked_glycosylation", "n_linked_glycosylation",
    ])
    parser.add_argument("--esm-checkpoint", required=True, help="Path to esm2_t33_650M_UR50D.pt")
    parser.add_argument("--custom-esm-dir", required=True, help="ESM feature cache (.npz per accession)")
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    train_ptm_dir = Path(args.train_ptm_dir)
    predict = _load_predict_module(train_ptm_dir)

    custom_esm_dir = Path(args.custom_esm_dir)
    custom_esm_dir.mkdir(parents=True, exist_ok=True)
    esm_path = _esm_cache_path(custom_esm_dir, args.protein_id, args.sequence)
    if not esm_path.is_file():
        features = _extract_esm_features(args.sequence, Path(args.esm_checkpoint))
        np.savez_compressed(
            esm_path, features=features, protein_id=args.protein_id,
            sequence=args.sequence, length=len(args.sequence),
        )

    # project_root = DeepPTMPred/ (train_ptm_dir = DeepPTMPred/pred/train_PTM)
    project_root = train_ptm_dir.parent.parent
    config = predict.PredictConfig(ptm_type=args.ptm_type, project_root=str(project_root))
    # Overwritten AFTER building the config (which sets its own default
    # relative to project_root) and BEFORE building the predictor (which
    # passes 'config' by reference to its internal data loader): the
    # attribute is read at call time, not copied beforehand.
    config.custom_esm_dir = str(custom_esm_dir)

    predictor = predict.PTMPredictor(config)

    target_aa = config.target_aa
    positions = [i + 1 for i, aa in enumerate(args.sequence) if aa in target_aa]

    if not positions:
        pd.DataFrame(columns=OUTPUT_COLUMNS).to_csv(args.out_csv, index=False)
        return 0

    results_df = predictor.predict_ptm_sites(
        args.protein_id, args.sequence, positions, pdb_path=args.pdb_path
    )
    results_df["protein_id"] = args.protein_id
    results_df["ptm_type"] = args.ptm_type
    results_df[OUTPUT_COLUMNS].to_csv(args.out_csv, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
