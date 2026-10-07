from __future__ import annotations

import csv
import math

import numpy as np

from gems47.geochem_consensus import (
    combine_geochemistry_and_structure,
    geochemistry_influence,
    read_consensus_points,
    structural_edge_agreement,
)


def _write_csv(path, rows):
    fields = [
        "name", "row", "col", "temp_c", "geothermquartz_c",
        "geothermchalc_c", "geothermcat_c", "dist_known_fault_px", "layer",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_reader_groups_duplicate_rows_and_ignores_label_distance(tmp_path):
    path = tmp_path / "gdr.csv"
    _write_csv(path, [
        {
            "name": "  Spring A ", "row": 20, "col": 30, "temp_c": 20,
            "geothermquartz_c": 100, "geothermchalc_c": 100,
            "geothermcat_c": 999, "dist_known_fault_px": 0.0, "layer": "chemistry",
        },
        {
            "name": "spring a", "row": 20, "col": 30, "temp_c": 24,
            "geothermquartz_c": 100, "geothermchalc_c": 100,
            "geothermcat_c": 999, "dist_known_fault_px": 999.0, "layer": "temperature",
        },
        {
            "name": "Spring B", "row": 40, "col": 50, "temp_c": 25,
            "geothermquartz_c": 130, "geothermchalc_c": 70,
            "geothermcat_c": "", "dist_known_fault_px": 0.0, "layer": "chemistry",
        },
        {
            "name": "Spring C", "row": 60, "col": 70, "temp_c": 25,
            "geothermquartz_c": 130, "geothermchalc_c": "",
            "geothermcat_c": "", "dist_known_fault_px": 0.0, "layer": "chemistry",
        },
        {
            "name": "Outside", "row": 999, "col": 999, "temp_c": 20,
            "geothermquartz_c": 120, "geothermchalc_c": 120,
            "geothermcat_c": "", "dist_known_fault_px": 0.0, "layer": "chemistry",
        },
    ])

    points, audit = read_consensus_points(path, (100, 100))

    assert len(points) == 1
    point = points[0]
    assert (point.row, point.col) == (20, 30)
    assert point.name == "spring a"
    assert point.reservoir_temperature_c == 100.0
    assert point.outlet_temperature_c == 22.0
    assert point.thermometer_spread_c == 0.0
    expected_weight = ((100.0 - 80.0) / 120.0) * ((100.0 - 22.0) / 120.0)
    assert math.isclose(point.weight, expected_weight)
    assert audit.csv_rows == 5
    assert audit.grouped_locations == 3
    assert audit.positive_weight_locations == 1
    assert audit.ignored_label_derived_column == "dist_known_fault_px"
    assert "dist_known_fault_px" not in audit.fields_used


def test_geochemistry_influence_respects_support_and_footprint():
    from gems47.geochem_consensus import GeochemPoint

    shape = (120, 120)
    footprint = np.ones(shape, dtype=bool)
    footprint[:, :5] = False
    point = GeochemPoint(
        name="site", row=60, col=60, reservoir_temperature_c=150.0,
        outlet_temperature_c=20.0, thermometer_spread_c=5.0,
        n_thermometers=2, weight=0.75,
    )
    surface, support, diagnostics = geochemistry_influence([point], shape, footprint)
    assert surface[60, 60] > surface[60, 70] > 0.0
    assert support[60, 60]
    assert not support[60, 4]
    assert not support[60, 101]
    assert diagnostics["support_pixels"] == int(support.sum())


def test_structural_edge_agreement_rewards_aligned_edges():
    height = width = 120
    yy, xx = np.mgrid[:height, :width].astype(np.float32)
    footprint = np.ones((height, width), dtype=bool)

    aligned, aligned_support, _ = structural_edge_agreement(xx, 2.0 * xx, footprint)
    crossed, crossed_support, _ = structural_edge_agreement(xx, yy, footprint)

    interior = (slice(20, -20), slice(20, -20))
    assert aligned_support[interior].all()
    assert crossed_support[interior].all()
    assert float(aligned[interior].mean()) > 0.99
    assert float(crossed[interior].mean()) < 1e-6


def test_interaction_is_zero_outside_joint_support():
    shape = (5, 6)
    geo = np.ones(shape, dtype=np.float32)
    edge = np.full(shape, 0.5, dtype=np.float32)
    geo_support = np.ones(shape, dtype=bool)
    edge_support = np.ones(shape, dtype=bool)
    footprint = np.ones(shape, dtype=bool)
    geo_support[1, 1] = False
    edge_support[2, 2] = False
    footprint[3, 3] = False

    score, valid = combine_geochemistry_and_structure(
        geo, geo_support, edge, edge_support, footprint
    )

    assert np.all(score[valid] == 0.5)
    assert not valid[1, 1]
    assert not valid[2, 2]
    assert not valid[3, 3]
