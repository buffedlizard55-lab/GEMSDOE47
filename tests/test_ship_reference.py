import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from gems47.grid import Template
from scripts.ship import read_reference_raster


@pytest.fixture
def template():
    return Template(
        shape=(2, 3),
        transform=Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        crs="EPSG:32611",
        footprint=np.ones((2, 3), dtype=bool),
        catalogue=np.zeros((2, 3), dtype=bool),
    )


def _write_raster(path, *, count=1, crs="EPSG:32611", transform=None, values=None):
    transform = transform or Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    if values is None:
        values = np.zeros((count, 2, 3), dtype=np.float32)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=3,
        count=count,
        dtype="float32",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(values)
    return path


def test_reference_reader_checks_band_and_template_grid(tmp_path, template):
    good = _write_raster(tmp_path / "good.tif", values=np.array([[[1, 0, 0], [0, 0, 0]]], dtype=np.float32))
    assert np.array_equal(read_reference_raster(good, template), [[1, 0, 0], [0, 0, 0]])

    two_bands = _write_raster(tmp_path / "two-bands.tif", count=2)
    with pytest.raises(ValueError, match="exactly one band"):
        read_reference_raster(two_bands, template)

    shifted = _write_raster(
        tmp_path / "shifted.tif",
        transform=Affine(100.0, 0.0, 243450.0, 0.0, -100.0, 4508550.0),
    )
    with pytest.raises(ValueError, match="grid does not match"):
        read_reference_raster(shifted, template)


def test_reference_reader_rejects_infinity_and_converts_nan_nodata(tmp_path, template):
    inf_values = np.zeros((1, 2, 3), dtype=np.float32)
    inf_values[0, 0, 0] = np.inf
    infinite = _write_raster(tmp_path / "infinite.tif", values=inf_values)
    with pytest.raises(ValueError, match="infinite values"):
        read_reference_raster(infinite, template)

    nan_values = np.zeros((1, 2, 3), dtype=np.float32)
    nan_values[0, 0, 0] = np.nan
    nodata = _write_raster(tmp_path / "nan.tif", values=nan_values)
    result = read_reference_raster(nodata, template)
    assert np.isfinite(result).all()
    assert result[0, 0] == 0.0
