#!/usr/bin/env python3
"""Run the frozen H47-C1 scarp-versus-channel screen on restored mirror bytes.

No upload, no live-score fitting, no hidden-label model. Every spacing/block
score is preserved. Only selection/calibration data choose the operating point;
test results cannot change it. Outputs are research-only regardless of a proxy
win because target exchangeability and organizer provenance remain unverified.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Limit OpenMP before importing sklearn/numpy; this sandbox has two CPUs.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

import joblib
import numpy as np
import rasterio
from scipy import ndimage
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from gems47 import grid as G
from gems47 import metric as M
from gems47 import profile as P
from gems47 import spatial_screen as B
from gems47.conformal import choose_operating_point, simultaneous_lower_bounds
from gemsdoe47.magnetic import greedy_spaced_pixels, ranked_pixels

SPACINGS = (1.5, 2.8, 3.6, 4.6, 5.8)
SEED = 470610
BUDGET = 37_654
CACHE = ROOT / ".cache" / "profile_screen"
PROTOCOL = ROOT / "docs" / "research" / "h47c-hypotheses-preregistered.md"
CODE_PATHS = (
    "scripts/run_profile_experiment.py", "src/gems47/profile.py", "src/gems47/spatial_screen.py",
    "src/gems47/conformal.py", "src/gems47/metric.py", "gemsdoe47/magnetic.py",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, values: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2, allow_nan=False) + "\n")


def _build_features(data: Path, hashes: dict) -> tuple[np.ndarray, np.ndarray, dict, np.ndarray]:
    meta_path = CACHE / "features.json"
    expected_names = [f"raw_{i}" for i in range(1, 20)] + list(P.STANDARD_NAMES) + list(P.PROFILE_NAMES)
    if meta_path.exists():
        old = json.loads(meta_path.read_text())
        if old.get("hashes") == hashes and old.get("names") == expected_names:
            x = np.load(CACHE / "features.npy", mmap_mode="r")
            idx = np.load(CACHE / "support_indices.npy")
            support = np.load(CACHE / "support.npy")
            if x.shape == (idx.size, len(expected_names)) and np.array_equal(np.flatnonzero(support), idx):
                print("[features] validated cache hit", flush=True)
                return x, idx, old, support
    with rasterio.open(data / "training_features.tif") as source:
        raw_valid = np.ones(source.shape, bool)
        for band in range(1, source.count + 1):
            v = source.read(band, masked=True)
            raw_valid &= ~np.ma.getmaskarray(v) & np.isfinite(v.data) & (v.data > -1e30)
        elevation = source.read(12, masked=True).filled(0).astype(np.float32)
        gravity = source.read(13, masked=True).filled(0).astype(np.float32)
    support = ndimage.minimum_filter(raw_valid.astype(np.uint8), size=41, mode="constant", cval=0) > 0
    support &= G.load_template(data).footprint
    idx = np.flatnonzero(support.ravel())
    if idx.size < 180_000:
        raise ValueError("insufficient complete feature support")
    x = np.lib.format.open_memmap(CACHE / "features.npy", mode="w+", dtype="float32",
                                shape=(idx.size, len(expected_names)))
    with rasterio.open(data / "training_features.tif") as source:
        for i in range(19):
            x[:, i] = source.read(i + 1).ravel()[idx]
    cursor = 19
    for builder in (P.ordinary_terrain, P.scarp_profiles):
        print(f"[features] {builder.__name__}", flush=True)
        layers = builder(elevation, support) if builder is P.ordinary_terrain else builder(elevation, gravity, support)
        for name, values in layers.items():
            if name != expected_names[cursor]:
                raise ValueError("feature order differs from frozen specification")
            x[:, cursor] = values.ravel()[idx]
            if not np.isfinite(x[:, cursor]).all():
                raise ValueError(f"non-finite feature: {name}")
            cursor += 1
        del layers
    x.flush()
    np.save(CACHE / "support_indices.npy", idx)
    np.save(CACHE / "support.npy", support)
    meta = {"hashes": hashes, "names": expected_names, "n_support": int(idx.size),
            "support_erosion": "41x41 minimum filter on all raw-band validity; 20 px per side",
            "shape": list(support.shape), "feature_columns": int(x.shape[1])}
    save_json(meta_path, meta)
    return x, idx, meta, support


def _fit_fields(x, idx, blocks, ids, labels, key: str) -> dict[str, np.ndarray]:
    train_ids = [b["block_id"] for b in blocks if b["role"] == "train"]
    train_mask = np.isin(ids, train_ids)
    target = B.training_target(labels, train_mask).ravel()[idx]
    tr_rows = np.flatnonzero(train_mask.ravel()[idx])
    samples, weights = B.sample_training_rows(target, tr_rows, seed=SEED)
    fields = {}
    for name, cols in (("raw", 19), ("structural", 19 + len(P.STANDARD_NAMES)), ("profile", x.shape[1])):
        field_path = CACHE / f"{name}-{key[:16]}.npy"
        model_path = CACHE / f"{name}-{key[:16]}.joblib"
        if field_path.exists() and model_path.exists():
            field = np.load(field_path)
            if field.shape == labels.shape and np.isfinite(field).all() and ((field >= 0) & (field <= 1)).all():
                fields[name] = field
                print(f"[fit] {name}: content-keyed cache hit", flush=True)
                continue
        print(f"[fit] {name}, rows={len(samples):,}, columns={cols}", flush=True)
        model = HistGradientBoostingRegressor(
            max_iter=150, learning_rate=.06, max_leaf_nodes=15, l2_regularization=2,
            min_samples_leaf=100, early_stopping=False, random_state=SEED,
        )
        with threadpool_limits(limits=2):
            model.fit(np.asarray(x[samples, :cols]), target[samples], sample_weight=weights)
            field = np.zeros(labels.shape, np.float32)
            for start in range(0, idx.size, 65_536):
                end = min(start + 65_536, idx.size)
                scores = model.predict(np.asarray(x[start:end, :cols]))
                if not np.isfinite(scores).all():
                    raise ValueError("non-finite model prediction")
                field.ravel()[idx[start:end]] = np.clip(scores, 0, 1).astype(np.float32)
        np.save(field_path, field)
        joblib.dump(model, model_path)
        fields[name] = field
    save_json(CACHE / "training-receipt.json", {
        "training_core_pixels": int(train_mask.sum()), "sample_rows": len(samples),
        "sample_positive_kernel_rows": int((target[samples] > 0).sum()),
        "inverse_sampling_weight_sum": float(weights.sum()),
        "no_labels_outside_training_cores_used": True, "content_key": key,
    })
    # Current chosen field is strictly from the training-only fit, never all-label refit.
    np.save(CACHE / "profile-field.npy", fields["profile"])
    return fields


def emit(field: np.ndarray, support: np.ndarray, spacing: float, count: int) -> np.ndarray:
    selected = greedy_spaced_pixels(ranked_pixels(field, support), field.shape,
                                    min_separation_px=spacing, budget=count)
    p = np.zeros(field.shape, np.float32)
    p.ravel()[selected] = 1
    if int(p.sum()) != count or (p[~support] != 0).any():
        raise ValueError("emission contract failed")
    return p


def main() -> int:
    started = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    data = G.data_dir()
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    inputs = {"training_features": data / "training_features.tif", "labels": data / "labels.tif",
              "sample_submission": data / "sample_submission.tif"}
    hashes = {name: digest(path) for name, path in inputs.items()}
    for name, sha in hashes.items():
        expected = next(e["sha256"] for e in manifest["files"] if e["id"] == name)
        if sha != expected:
            raise ValueError(f"input hash mismatch: {name}")
    code_hashes = {p: digest(ROOT / p) for p in CODE_PATHS}
    key_data = {"inputs": hashes, "code": code_hashes, "protocol": digest(PROTOCOL)}
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    t = G.load_template(data)
    with rasterio.open(data / "labels.tif") as source:
        labels = source.read(1)
    x, idx, meta, support = _build_features(data, key_data)
    blocks, ids = B.spatial_blocks(support, seed=SEED)
    for block in blocks:
        y0, y1, x0, x1 = block["bounds_rc"]
        block["catalogue_truth_pixels"] = int(((labels[y0:y1, x0:x1] == 1) & support[y0:y1, x0:x1]).sum())
        block["budget"] = B.block_budget(block, int(support.sum()), BUDGET)
    save_json(ROOT / "evidence" / "profile-blocks.json", {"blocks": blocks, "seed": SEED,
              "protocol_sha256": key_data["protocol"], "assigned_without_truth_stratification": True})
    block_digest = digest(ROOT / "evidence" / "profile-blocks.json")
    fields = _fit_fields(x, idx, blocks, ids, labels, key)
    rows = []
    # Candidate selection/calibration complete BEFORE any test rows are scored.
    for role in ("selection", "calibration", "test"):
        for block in [b for b in blocks if b["role"] == role]:
            y0, y1, x0, x1 = block["bounds_rc"]
            sy, sx = slice(y0, y1), slice(x0, x1)
            valid = support[sy, sx]
            truth = (labels[sy, sx] == 1) & valid
            random_field = np.random.default_rng(SEED + block["block_id"]).random(valid.shape, dtype=np.float32)
            for name in ("raw", "structural", "profile", "random"):
                f = random_field if name == "random" else fields[name][sy, sx]
                for sweep_spacing in SPACINGS:
                    p = emit(f, valid, sweep_spacing, block["budget"])
                    result = M.score(p, truth, valid).as_dict()
                    # Store finite primitive components only; zero scores have no inv_dti.
                    row = {k: result[k] for k in ("TP_w", "FP_w", "FN_w", "|G|", "S", "Phi", "DTI")}
                    row.update(role=role, block_id=block["block_id"], model=name, spacing_px=sweep_spacing,
                               valid_pixels=block["support_pixels"], prediction_pixels=block["budget"])
                    rows.append(row)
        if role == "calibration":
            def matrix(model, wanted_role):
                return np.array([[next(r["DTI"] for r in rows if r["model"] == model
                                      and r["role"] == wanted_role and r["block_id"] == b["block_id"]
                                      and r["spacing_px"] == s) for s in SPACINGS]
                                 for b in blocks if b["role"] == wanted_role])
            band = simultaneous_lower_bounds(matrix("profile", "selection"), matrix("profile", "calibration"), coverage=.90)
            chosen = choose_operating_point(band, SPACINGS)
            spacing = SPACINGS[chosen]
            baseline_options = []
            for model in ("raw", "structural"):
                for s in SPACINGS:
                    rs = [r for r in rows if r["role"] == "selection" and r["model"] == model and r["spacing_px"] == s]
                    baseline_options.append((B.pool(rs), model, s))
            _, incumbent, incumbent_spacing = max(baseline_options)
            print(f"[locked before test] profile d={spacing}px; incumbent={incumbent} d={incumbent_spacing}px; "
                  f"90% conditional floor={band['lower_bounds'][chosen]:.6f}", flush=True)
            save_json(CACHE / "locked-choice.json", {"spacing_px": spacing, "incumbent": incumbent,
                      "incumbent_spacing_px": incumbent_spacing, "conformal": band, "test_not_yet_scored": True})
        print(f"[score] {role} complete", flush=True)
    if spacing != SPACINGS[choose_operating_point(band, SPACINGS)]:
        raise ValueError("spacing changed after it was locked; refusing test interpretation")
    locked_choice = json.loads((CACHE / "locked-choice.json").read_text())
    if spacing != locked_choice["spacing_px"] or incumbent_spacing != locked_choice["incumbent_spacing_px"]:
        raise ValueError("final interpretation differs from pre-test lock")
    def chosen_rows(model, selected_spacing):
        return [r for r in rows if r["role"] == "test" and r["model"] == model and r["spacing_px"] == selected_spacing]
    verdict = B.gate(chosen_rows("profile", spacing), chosen_rows(incumbent, incumbent_spacing),
                     chosen_rows("random", spacing), band["lower_bounds"][chosen])
    # Independent off-catalogue geological compilation: diagnostic only, never a tuner.
    with rasterio.open(data / "external" / "derived_sgmc_faults_100m_u8.tif") as source:
        sgmc = source.read(1) > 0
    dc = ndimage.distance_transform_edt(~t.catalogue)
    sgmc &= t.evaluated & (dc > 3)
    with rasterio.open(data / "reference" / "h33-2-b2-zeros.tif") as source:
        h33 = source.read(1) > 0
    h33_field = (1 / (1 + ndimage.distance_transform_edt(~h33))).astype(np.float32)
    secondary = []
    for block in [b for b in blocks if b["role"] == "test"]:
        y0, y1, x0, x1 = block["bounds_rc"]
        sy, sx = slice(y0, y1), slice(x0, x1)
        valid = support[sy, sx] & t.evaluated[sy, sx]
        truth = sgmc[sy, sx] & valid
        random_field = np.random.default_rng(SEED + block["block_id"]).random(valid.shape, dtype=np.float32)
        for name, field, s in (("profile", fields["profile"][sy, sx], spacing),
                               (incumbent, fields[incumbent][sy, sx], incumbent_spacing),
                               ("random", random_field, spacing),
                               ("h33_geometry_reemitted", h33_field[sy, sx], spacing)):
            p = emit(field, valid, s, block["budget"])
            sc = M.score(p, truth, valid)
            secondary.append({"block_id": block["block_id"], "model": name, "spacing_px": s,
                              "TP_w": sc.T, "FP_w": sc.F, "FN_w": sc.FN, "|G|": sc.K,
                              "S": sc.S, "Phi": sc.Phi, "DTI": sc.DTI})
    sgmc_summary = {name: B.pool([r for r in secondary if r["model"] == name])
                    for name in sorted({r["model"] for r in secondary})}
    # Global inference is transparent: same frozen field/spacing, global rather
    # than proportional per-block quota. It is NOT the target of the block band.
    artifact = emit(fields["profile"], support & t.evaluated, spacing, BUDGET)
    np.save(CACHE / "candidate.npy", artifact)
    candidate_mask_sha = hashlib.sha256(np.packbits(artifact.ravel() > 0).tobytes()).hexdigest()
    summary = {
        "schema_version": 1, "hypothesis_id": "H47-C1", "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_sha256": key_data["protocol"], "code_sha256": code_hashes,
        "input_sha256": hashes, "block_assignment_sha256": block_digest,
        "official_inputs_authenticated": False, "all_private_label_or_live_score_claims": None,
        "feature_metadata": meta, "budget": BUDGET, "spacings_px": list(SPACINGS),
        "selected_spacing_px": spacing, "incumbent_model": incumbent,
        "incumbent_spacing_px": incumbent_spacing, "conformal": band, "screen_gate": verdict,
        "block_counts": {role: sum(b["role"] == role for b in blocks) for role in B.ROLES},
        "truth_bearing_block_counts": {role: sum(b["role"] == role and b["catalogue_truth_pixels"] > 0 for b in blocks)
                                      for role in B.ROLES},
        "catalogue_total_truth_pixels": int(t.catalogue.sum()),
        "catalogue_truth_on_feature_support": int((t.catalogue & support).sum()),
        "catalogue_truth_on_guarded_cores": int((t.catalogue & (ids >= 0)).sum()),
        "catalogue_test_truth_pixels": sum(r["|G|"] for r in chosen_rows("profile", spacing)),
        "secondary_sgmc_pooled_dti": sgmc_summary,
        "secondary_sgmc_label_rule": "SGMC mirror AND not catalogue AND distance(catalogue)>3px; diagnostic only",
        "secondary_sgmc_rows": secondary,
        "candidate_mask_sha256": candidate_mask_sha,
        "candidate_prediction_pixels": int(artifact.sum()),
        "artifact_emission_rule": "same training-only field and chosen spacing; global 37,654-dot quota, exact catalogue pixels excluded",
        "conformal_target_does_not_include_global_artifact": True,
        "artifact_exclusion": "20px feature-validity erosion; no claims on omitted areas",
        "training_receipt": json.loads((CACHE / "training-receipt.json").read_text()),
        "limitations": [
            "All public labels were accessible to prior sessions; this is a frozen re-screen, not pristine new labels.",
            "The block band does not certify the global-quota artifact, private labels, or pooled map DTI.",
            "Spatial exchangeability unverified; no guaranteed positive leaderboard floor is available.",
            "Mirrors are reproducible but not organizer-authenticated.",
            "No weekly submission slot spent. Negative results cannot be relabeled as approved.",
        ], "elapsed_seconds": round(time.time() - started, 2),
    }
    history = ROOT / "evidence" / "profile-spacing-history.csv"
    with history.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary["score_history_sha256"] = digest(history)
    save_json(ROOT / "evidence" / "profile-screen.json", summary)
    save_json(CACHE / "screen-all-rows.json", {"rows": rows})
    print(json.dumps({"selected_spacing": spacing, "gate": verdict, "sgmc": sgmc_summary,
                      "elapsed_seconds": summary["elapsed_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
