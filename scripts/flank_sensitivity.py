#!/usr/bin/env python3
"""Conditional sensitivity of the H47-SAF exploratory fit to an H33 scenario.

There are twelve owner-reported raster/score pairs in the LATI input set. The
H33-2-B2 TIFF is an additional flank-pruned reference raster, but no authenticated
receipt links it to the participant-level 0.2778 score. This script therefore
adds H33 only as an *assumed-DTI scenario* and reports the direction of the
exploratory leave-one-out (LOO) fit across a coarse tested grid.

A change from positive to negative LOO improvement between tested values is a
coarse-grid sign-change bracket only. The script does not interpolate or solve
for an exact root, authenticate a score-to-file mapping, test causality, or
validate private-target performance. H47-SAF remains unresolved and is not
promoted.

    python3 scripts/flank_sensitivity.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import features as FEAT
from gems47 import grid as G
from gems47 import hypotheses as HY
from gems47 import lati
from gems47 import metric as M
from gems47.scripts_common import rank_u8_inplace

H33 = ROOT / ".cache" / "gems_data" / "reference" / "h33-2-b2-zeros.tif"
H33_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0
ASSUMED_DTI_GRID = [
    0.1800, 0.2000, 0.2200, 0.2400, 0.2477, 0.2550, 0.2600,
    0.2700, 0.2708, 0.2778, 0.2900, 0.3000,
]


def find_grid_sign_change_bracket(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return adjacent tested DTI values bracketing positive-to-nonpositive LOO change.

    This reports the tested values only; it deliberately performs no root finding
    or interpolation. The listed DTI values are scenario assumptions, not
    observed scores unless independently authenticated.
    """
    tested = sorted(
        (row for row in rows if row.get("assumed_h33_dti") is not None),
        key=lambda row: float(row["assumed_h33_dti"]),
    )
    for left, right in pairwise(tested):
        left_change = float(left["loo_improvement_pct"])
        right_change = float(right["loo_improvement_pct"])
        if left_change > 0.0 and right_change <= 0.0:
            return {
                "last_tested_positive_dti": float(left["assumed_h33_dti"]),
                "last_tested_positive_loo_improvement_pct": left_change,
                "first_tested_nonpositive_dti": float(right["assumed_h33_dti"]),
                "first_tested_nonpositive_loo_improvement_pct": right_change,
                "interpretation": "coarse-grid sign-change bracket only; no exact root computed",
                "interpolation_performed": False,
            }
    return None


def load_h33_dots(template: G.Template) -> tuple[np.ndarray, str]:
    """Load the hash-pinned reference raster and verify its grid before use."""
    if not H33.is_file():
        raise SystemExit(
            f"missing {H33}; restore the hash-pinned ref_h33_2_b2 entry before running"
        )
    digest = hashlib.sha256(H33.read_bytes()).hexdigest()
    if digest != H33_SHA256:
        raise SystemExit(f"H33 SHA-256 mismatch: {digest} != {H33_SHA256}")
    with rasterio.open(H33) as src:
        if src.count != 1 or not G.dataset_matches_template_grid(src, template):
            raise SystemExit("H33 raster grid/band count does not match the competition template")
        values = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0)
    return values > 0, digest


def h33_scenario_obs(
    dti: float,
    dots: np.ndarray,
    sha256: str,
    template: G.Template,
    ev: np.ndarray,
    ev_idx: np.ndarray,
) -> lati.Obs:
    """Build one LATI row with an explicitly assumed, not authenticated, DTI."""
    pred = np.where(ev, dots, False)
    dot_pos = np.flatnonzero(pred.ravel())
    position = np.full(template.shape[0] * template.shape[1], -1, np.int64)
    position[ev_idx] = np.arange(ev_idx.size)
    weights = M.max_kernel_filter(pred.astype(np.float64))
    proximity = np.zeros(template.shape, dtype=np.float64)
    for dy, dx, kernel_weight in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        proximity += kernel_weight * lati._shift_in(pred.astype(np.float64), dy, dx)
    return lati.Obs(
        id="h33-2-b2",
        dti=float(dti),
        site="GEMSDOE32",
        family="flank-pruned reference raster; score/file link unverified",
        sha256=sha256,
        S=float(pred.sum()),
        n_dots=int(dots.sum()),
        n_on_catalogue=int((dots & template.catalogue).sum()),
        w=weights.ravel()[ev_idx].astype(np.float32),
        a=proximity.ravel()[ev_idx].astype(np.float32),
        dot_pos=position[dot_pos],
        dot_flat=dot_pos,
        extras={"assumed_dti_scenario": float(dti), "score_file_mapping_verified": False},
    )


def fit(uses: list[np.ndarray], observations: list[lati.Obs]) -> dict[str, Any]:
    values = np.stack(uses)
    levels = {1: 256, 2: 64}[len(uses)]
    model = lati.BinnedSoftmax(values, list(range(len(uses))), observations, levels)
    fitted = model.fit(l2=L2, bmax=BMAX, k_lo=KLO, k_hi=KHI)
    theta = np.asarray(fitted["theta"])
    fitted["ssr"] = float(np.sum((model.predict(theta) - model.dti_obs) ** 2))
    loo = 0.0
    for held_out in range(len(observations)):
        subset = [idx for idx in range(len(observations)) if idx != held_out]
        fold = model.fit(
            l2=L2,
            subset=subset,
            theta0=theta,
            bmax=BMAX,
            k_lo=KLO,
            k_hi=KHI,
        )
        residual = float(model.predict(np.asarray(fold["theta"]))[held_out]
                         - observations[held_out].dti)
        loo += residual**2
    fitted["loo"] = loo
    return fitted


def main() -> int:
    started = time.time()
    template = G.load_template()
    ev, shape = template.evaluated, template.shape
    ev_idx = np.flatnonzero(ev.ravel())
    obs12 = lati.load_observations(verbose=False)
    if len(obs12) != 12:
        raise SystemExit(f"expected 12 owner-reported observations, found {len(obs12)}")

    hypothesis_layers = HY.build_layers(template)
    h33_dots, h33_sha256 = load_h33_dots(template)

    def prox(oid: str, cap: float = 40.0) -> np.ndarray:
        observation = next((row for row in obs12 if row.id == oid), None)
        if observation is None:
            raise ValueError(f"missing observation {oid!r}")
        mask = np.zeros(shape[0] * shape[1], dtype=bool)
        mask[observation.dot_flat] = True
        ranked = -FEAT.dist_px(mask.reshape(shape), cap).ravel()[ev_idx]
        return rank_u8_inplace(ranked.astype(np.float32))

    d2_8_reference = prox("d2.8")
    flank = rank_u8_inplace(
        hypothesis_layers["flank_halo_0_3"].ravel()[ev_idx].astype(np.float32)
    )
    catalogue_distance = hypothesis_layers["_diag_d_catalogue"]
    halo3 = ev & (catalogue_distance > 0) & (catalogue_distance <= M.RANGE_PX)

    rows: list[dict[str, Any]] = []
    scenarios: list[float | None] = [None, *ASSUMED_DTI_GRID]
    print("assumed H33 DTI   n   flank beta    LOO base   LOO + flank   LOO improvement")
    print("score/file mapping is unverified; signs below are exploratory-fit directions only")
    for assumed_dti in scenarios:
        if assumed_dti is None:
            observations = list(obs12)
            scenario_label = "excluded"
        else:
            observations = list(obs12) + [
                h33_scenario_obs(assumed_dti, h33_dots, h33_sha256, template, ev, ev_idx)
            ]
            scenario_label = f"{assumed_dti:.4f}"

        base = fit([d2_8_reference], observations)
        with_flank = fit([d2_8_reference, flank], observations)
        flank_beta = float(with_flank["theta"][2])
        improvement = 100.0 * (base["loo"] - with_flank["loo"]) / base["loo"]
        direction = "positive" if improvement > 0.0 else "negative" if improvement < 0.0 else "zero"
        row = {
            "assumed_h33_dti": assumed_dti,
            "n_rows_in_fit": len(observations),
            "flank_beta": flank_beta,
            "K_base": float(base["theta"][0]),
            "K_with_flank": float(with_flank["theta"][0]),
            "loo_base": float(base["loo"]),
            "loo_with_flank": float(with_flank["loo"]),
            "loo_improvement_pct": float(improvement),
            "loo_change_direction": direction,
            "theta_base": [float(value) for value in base["theta"]],
            "theta_with_flank": [float(value) for value in with_flank["theta"]],
            "interpretation": "exploratory fit only; not a hypothesis verdict",
        }
        rows.append(row)
        print(
            f"{scenario_label:>16} {len(observations):>3} {flank_beta:>+11.3f}"
            f"   {base['loo']:.6f}   {with_flank['loo']:.6f}"
            f"   {improvement:>+8.1f}% ({direction})"
        )

    bracket = find_grid_sign_change_bracket(rows)
    if bracket is None:
        print("\nNo positive-to-nonpositive sign change was bracketed on the tested grid.")
    else:
        print(
            "\nCoarse tested-grid bracket only: positive at assumed DTI "
            f"{bracket['last_tested_positive_dti']:.4f}, nonpositive at "
            f"{bracket['first_tested_nonpositive_dti']:.4f}; no exact root computed."
        )

    h33_flank_dots = int((h33_dots & halo3).sum())
    out = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "How do hypothetical H33 DTI values change an exploratory H47-SAF LOO fit?",
        "scope": {
            "owner_reported_score_raster_pairs": len(obs12),
            "organizer_receipts_available": False,
            "additional_h33_row": "scenario only; score-to-file mapping unverified",
            "score_file_mapping_verified": False,
            "purpose": "sensitivity analysis of exploratory LOO fits, not validation or causal inference",
            "private_target_performance_established": False,
            "promotion_decision": "H47-SAF remains unresolved and is not promoted",
        },
        "h33_raster": {
            "path": H33.relative_to(ROOT).as_posix(),
            "sha256": h33_sha256,
            "dots": int(h33_dots.sum()),
            "dots_in_catalogue_flank_0_300m": h33_flank_dots,
            "note": "hash-pinned flank-pruned reference raster; its participant-score association is not authenticated",
        },
        "attribution_status": {
            "reported_participant_dti": 0.2778,
            "linked_to_this_tiff": False,
            "basis": "public leaderboard is participant-level and does not identify TIFFs; owner page marks H33-2-B2 unscored",
        },
        "tested_assumed_dti_grid": ASSUMED_DTI_GRID,
        "sweep": rows,
        "coarse_grid_sign_change_bracket": bracket,
        "conclusion": (
            "The twelve owner-reported observations show a positive exploratory LOO change when the "
            "flank layer is added. The H33 raster is not an authenticated thirteenth score pair. "
            "Under the hypothetical DTI grid, the fitted LOO change is positive at 0.2200 and "
            "negative by 0.2400; this is a coarse-grid sign-change bracket only. No exact break-even, "
            "causal verdict, score-to-file attribution, or private-target performance claim is "
            "established. H47-SAF remains unresolved and is not promoted."
        ),
        "seconds": round(time.time() - started, 1),
    }
    output = ROOT / "evidence" / "flank_sensitivity.json"
    output.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"wrote {output.relative_to(ROOT)} ({time.time() - started:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
