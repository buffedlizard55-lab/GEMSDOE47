from types import SimpleNamespace

import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine

from gems47.grid import Template, dataset_matches_template_grid

_DEFAULT_CRS = object()


def _template() -> Template:
    return Template(
        shape=(2, 3),
        transform=Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        crs="EPSG:32611",
        footprint=np.ones((2, 3), dtype=bool),
        catalogue=np.zeros((2, 3), dtype=bool),
    )


def _dataset(*, shape=(2, 3), crs=_DEFAULT_CRS, transform=None):
    if crs is _DEFAULT_CRS:
        crs = CRS.from_epsg(32611)
    return SimpleNamespace(
        shape=shape,
        crs=crs,
        transform=transform or Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
    )


def test_dataset_matches_template_grid_accepts_small_absolute_roundoff():
    template = _template()
    transform = Affine(100.0, 0.0, 243350.0 + 5e-10, 0.0, -100.0, 4508550.0)
    assert dataset_matches_template_grid(_dataset(transform=transform), template)


def test_dataset_matches_template_grid_rejects_wrong_transform_shape_or_crs():
    template = _template()
    wrong_transform = Affine(100.0, 0.0, 243350.001, 0.0, -100.0, 4508550.0)
    assert not dataset_matches_template_grid(_dataset(transform=wrong_transform), template)
    assert not dataset_matches_template_grid(_dataset(shape=(3, 2)), template)
    assert not dataset_matches_template_grid(_dataset(crs=CRS.from_epsg(32610)), template)
    assert not dataset_matches_template_grid(_dataset(crs=None), template)
