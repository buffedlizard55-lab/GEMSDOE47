#!/usr/bin/env python3
"""Audit the original selection-only H50 choice; never filter on calibration outcomes.

All H49 blocks were previously examined. Arithmetic is reproducible, but these are
exploratory diagnostics, not a fresh validation set or certified private score.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / 'evidence' / 'h50'


def conformal_floor(vals_sorted: list[float], alpha: float = 0.1) -> dict:
    if not 0 < alpha < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    a = np.asarray(vals_sorted, float)
    if a.ndim != 1 or not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
        raise ValueError('finite scores in [0,1] required')
    n = len(a)
    k = math.floor(alpha * (n + 1))
    return dict(n=n, k=k, floor=float(np.sort(a)[k - 1]) if k else 0.0,
                nominal_level=1-alpha, rank_coverage=(n+1-k)/(n+1))


def summarize(rows):
    groups = {}
    for r in rows:
        if r['arm'] == 'RANDOM_fixed_seed':
            continue
        key = (r['arm'], r['emitter'], float(r['spacing_px']), float(r['flank_b']))
        groups.setdefault(key, {'selection': [], 'calibration': []})[r['half']].append(float(r['dti']))
    # Calibration values cannot change which point is chosen.
    key = min(groups, key=lambda k: (-np.mean(groups[k]['selection']), k[2], k[0], k[1], k[3]))
    arm, emitter, spacing, flank = key
    selected = groups[key]
    cert = conformal_floor(selected['calibration'])
    return dict(chosen=dict(arm=arm, emitter=emitter, spacing_px=spacing, flank_b=flank,
                            selection_mean=float(np.mean(selected['selection'])),
                            calibration_mean=float(np.mean(selected['calibration']))),
                conformal=cert, calibration_scores=sorted(selected['calibration']))


def main():
    with (EV / 'spacing_sweep_h50.csv').open() as f:
        result = summarize(list(csv.DictReader(f)))
    result.update(
        status='EXPLORATORY_NOT_CERTIFIED', slot_authorized=False,
        formal_coverage_established=False,
        selection_rule='Maximise selection-half mean only, then inspect calibration once.',
        limitations=[
            'Same 39 public SGMC proxy blocks and seed as H49; not fresh untouched validation.',
            'Block exchangeability and relevance to private faults are unverified.',
            'Global emission is not covered by block-level calibration.',
            'Some large-spacing arms emit below quota; sweep is budget-capped, not exactly mass-matched.',
        ],
        withdrawn_draft=dict(
            lower_bound=0.03183577869822368,
            reason='Draft filtered candidates using calibration floors after inspecting results. '
                   'That selects on calibration; the claimed 90% guarantee is withdrawn. '
                   'The different scatter-greedy export was never validated by this sweep.'),
    )
    (EV / 'conformal_certificate_h50.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
