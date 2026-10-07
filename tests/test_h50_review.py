import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('h50_cert', ROOT/'scripts/certify_h50.py')
cert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cert)


def test_small_calibration_uses_vacuous_floor():
    for n in range(9):
        assert cert.conformal_floor([.2]*n)['floor'] == 0
    assert cert.conformal_floor([.2]*19)['k'] == 2


def test_selection_is_invariant_to_calibration():
    rows = []
    for arm, score in [('a', .3), ('b', .2)]:
        for half in ['selection', 'calibration']:
            rows.append(dict(arm=arm, emitter='disk', spacing_px=2.8, flank_b=3,
                             half=half, dti=score))
    original = cert.summarize(rows)['chosen']['arm']
    for r in rows:
        if r['half'] == 'calibration':
            r['dti'] = 0 if r['arm'] == 'a' else 1
    assert cert.summarize(rows)['chosen']['arm'] == original == 'a'


def test_h50_artifact_contract_and_no_promotion():
    import hashlib
    import json
    import zipfile

    import numpy as np
    import rasterio

    receipt = json.loads((ROOT/'docs/data/h50-submission.json').read_text())
    path = ROOT/'docs/downloads'/receipt['filename']
    assert receipt['artifact_role'] == 'finite_internal_mask_range_diagnostic'
    assert not receipt['slot_authorized']
    assert not receipt['submission_eligible']
    assert not receipt['conformal']['formal_coverage_established']
    assert receipt['conformal']['conformal']['floor'] == 0
    assert 'DO NOT UPLOAD' in receipt['note']
    assert len(receipt['note']) <= 200
    assert receipt['format_validation']['format_valid']
    assert len(receipt['format_validation']['checks']) == 15
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt['format_validation']['sha256']
    with rasterio.open(path) as ds:
        a = ds.read(1)
        mask = ds.read_masks(1) > 0
        assert ds.count == 1 and ds.dtypes == ('float32',)
        assert ds.shape == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all()
        assert (a > 0).sum() == 37612
        assert (~mask).sum() == 7111787
        assert not a[~mask].any()
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist() == [path.name]
        assert z.read(path.name) == path.read_bytes()
    assert receipt['uniqueness']['exact_matches'] == 0
    assert all(not c['exact'] for c in receipt['uniqueness']['comparisons'])


def test_h50_template_nanoutside_checkpoint_matches_the_mirrored_template_but_is_not_promoted():
    import hashlib
    import json
    import math
    import zipfile

    import numpy as np
    import rasterio

    receipt = json.loads((ROOT/'docs/data/h50-template-nanoutside.json').read_text())
    path = ROOT/'docs/downloads'/receipt['filename']
    assert receipt['artifact_role'] == 'template_nanoutside_format_checkpoint'
    assert receipt['format_status'] == 'LOCAL_TEMPLATE_MATCH_PASS; ORGANIZER_ACCEPTANCE_UNVERIFIED'
    assert not receipt['slot_authorized']
    assert not receipt['submission_eligible']
    assert receipt['same_prediction_mask_as'].endswith('research-finite-mask.tif')
    assert receipt['strict_template_validation']['status'] == 'LOCAL_PASS'
    assert receipt['strict_template_validation']['non_nan_outside_pixels'] == 0
    assert receipt['strict_template_validation']['below_zero_pixels'] == 0
    assert receipt['strict_template_validation']['above_one_pixels'] == 0
    assert receipt['format_validation']['required_local_checks_passed']
    assert not receipt['format_validation']['passes_nan_intolerant_range_check']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt['strict_template_validation']['sha256']
    with rasterio.open(path) as ds:
        values = ds.read(1)
        mask = ds.read_masks(1) > 0
        assert ds.count == 1 and ds.dtypes == ('float32',)
        assert ds.shape == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert math.isnan(ds.nodata)
        assert np.isfinite(values[mask]).all()
        assert ((values[mask] >= 0) & (values[mask] <= 1)).all()
        assert int(np.isnan(values).sum()) == 7111787
        assert not mask[~np.isfinite(values)].any()
        assert int((values > 0).sum()) == 37612
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist() == [path.name]
        assert z.read(path.name) == path.read_bytes()
