"""Regression: a spacing sweep must not overwrite the pre-test locked choice."""
import ast
from pathlib import Path


def test_sweep_loop_never_rebinds_the_locked_spacing():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_profile_experiment.py"
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Name) and node.iter.id == "SPACINGS":
            assert isinstance(node.target, ast.Name)
            assert node.target.id != "spacing", "test sweep overwrites the pre-test operating point"
    source = path.read_text()
    assert "spacing != locked_choice[\"spacing_px\"]" in source
    assert "spacing != SPACINGS[choose_operating_point(band, SPACINGS)]" in source
