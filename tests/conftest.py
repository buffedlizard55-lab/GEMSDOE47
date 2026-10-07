import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_data: requires the restored 1.2 GB competition bytes")


def pytest_runtest_setup(item):
    """Skip explicitly data-dependent tests in a clean checkout before they open absent rasters."""
    if item.get_closest_marker("needs_data") is None:
        return
    import pytest

    from gems47.grid import data_dir

    required = (data_dir() / "labels.tif", data_dir() / "sample_submission.tif")
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        pytest.skip(f"restored competition inputs absent ({', '.join(missing)}); run restore_data.py")
