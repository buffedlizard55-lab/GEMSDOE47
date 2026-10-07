#!/usr/bin/env python3
"""Generate new H50a research inference with finite samples and internal null mask.

No old submission raster is used as a model input. Does not authorize a slot.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems47 import contract as C
from gems47 import grid as G
from gems47s3 import emission as E
from gems47s3 import geomorph
from gems47s3.detector import Bands, Recipe, build_core
from gems47s3.grid import Grid


def main():
    certificate = json.loads((ROOT / 'evidence/h50/conformal_certificate_h50.json').read_text())
    choice = certificate['chosen']
    if choice['arm'] != 'H50a_corridor' or choice['emitter'] != 'disk':
        raise ValueError('This research builder implements only the original selected H50a disk arm')
    dd = ROOT / '.cache/gems_data'
    g = Grid(dd)
    valid = g.all_bands_finite()
    template = G.load_template()
    spec = importlib.util.spec_from_file_location('h50', ROOT / 'scripts/run_h50.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recipe = Recipe(name='R7_scarp9_polarity', terms=[
        ('det_elev_slope', 'scarp', 9., 3.), ('det_elev_slope', 'polarity', 9., 2.),
        ('det_elev_slope', 'curv', 2.5, 1.), ('det_elev_slope', 'detrend', 2.5, 1.),
        ('det_elev_slope', 'slope_var', 5., 1.)])
    core = build_core(recipe, Bands(dd / 'training_features.tif'), valid)['core']
    prior = module.reservoir_corridor_prior(dd, valid)['prior']
    field = module.combine_terms([(core, 1.)], valid) * (.35 + .65 * prior)
    field = np.where(valid, geomorph.rank_scale(np.where(valid, field, np.nan)), 0).astype('float32')
    allowed = valid & template.footprint & (g.d_catalogue > choice['flank_b'])
    dots = E.nms_disk(field, allowed, choice['spacing_px'])
    budget = round(7.37 * int((valid & ~g.catalogue).sum()) / 1000)
    if dots.sum() > budget:
        dots = E.topk_mask(field, budget, dots)
    digest = hashlib.sha256(np.packbits(dots).tobytes()).hexdigest()
    stem = f'gems47-h50a-corridor-s1p5-b3-20261007-{digest[:12]}-research-finite-mask'
    path = ROOT / 'docs/downloads' / (stem + '.tif')
    comparisons = []
    paths = sorted((ROOT / 'docs/downloads').rglob('*.tif'))
    paths += sorted(dd.glob('scored/*.tif')) + sorted(dd.glob('reference/*.tif'))
    paths += sorted((ROOT / 'submission').glob('*.tif'))
    for other in paths:
        if other == path:
            continue
        with rasterio.open(other) as ds:
            if ds.count != 1 or ds.shape != dots.shape or ds.transform != template.transform:
                continue
            a = ds.read(1)
        mask = np.isfinite(a) & (a > 0)
        union = (mask | dots).sum()
        comparisons.append(dict(path=str(other.relative_to(ROOT)), sha256=C.sha256(other),
                                exact=bool(np.array_equal(mask, dots)),
                                jaccard=float((mask & dots).sum() / union) if union else 1.))
    if any(r['exact'] for r in comparisons):
        raise ValueError('Exact positive-mask match to prior artifact; no unique claim permitted')
    if path.exists():
        with rasterio.open(path) as ds:
            if not np.array_equal(ds.read(1), dots):
                raise ValueError('Existing artifact differs')
        audit = C.validate(path, template)
    else:
        audit = C.write(dots.astype('float32'), path, template,
                        tags={'STATUS': 'RESEARCH_ONLY_DO_NOT_UPLOAD', 'METHOD': 'H50a corridor'})
    if not audit['format_valid']:
        raise ValueError(audit['failed_checks'])
    archive = C.single_tiff_zip(path, path.with_suffix('.zip'))
    note = ('H50a corridor; s=1.5px/150m; nominal 90% proxy floor=0.0000; '
            'coverage unverified; finite+mask; UNSCORED; NOT PROMOTED; DO NOT UPLOAD')
    receipt = dict(status='RESEARCH_ONLY_NOT_PROMOTED', slot_authorized=False,
                   submission_eligible=False, organizer_acceptance_verified=False,
                   filename=path.name, name=f'GEMSDOE47-H50a-{digest[:12]}', note=note,
                   format_validation=audit, zip=archive, selection=choice,
                   conformal=certificate, uniqueness=dict(comparisons=comparisons,
                       exact_matches=0, max_jaccard=max(r['jaccard'] for r in comparisons),
                       scope='Only listed local/restored rasters; not the old 561-comparison C1 audit'),
                   emission=dict(n_dots=int(dots.sum()), budget=budget,
                                 global_emission_not_block_certificate=True))
    for destination in [path.with_suffix('.json'), ROOT / 'evidence/h50/submission_build_h50.json',
                        ROOT / 'docs/data/h50-submission.json']:
        C.save_receipt(destination, receipt)
    path.with_suffix('.txt').write_text(note+'\n')
    print(json.dumps({k:receipt[k] for k in ['filename','name','note','emission']}, indent=2))


if __name__ == '__main__':
    main()
