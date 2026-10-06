#!/usr/bin/env python3
"""Retrieve three public official archives and measure geometry/grid coverage.

Research-feasibility audit only. No private data or submission endpoint. Raw
archives stay ignored; only source/license/hash/coverage receipts are published.
HTTPS certificate verification is never disabled. Runs on a GitHub-hosted runner
as well as locally, so sandbox-only network failures are not mistaken for 404s.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import rasterio
import requests
import shapefile
from rasterio.features import rasterize
from rasterio.warp import transform_geom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47 import grid as G

SOURCES = [
    {"id": "usgs_qffd", "publisher": "USGS", "license": "USGS public data; source attribution retained",
     "source_page": "https://www.usgs.gov/programs/earthquake-hazards/faults",
     "url": "https://earthquake.usgs.gov/static/lfs/nshm/qfaults/Qfaults_GIS.zip"},
    {"id": "ingenious_qfaults", "publisher": "DOE Geothermal Data Repository / INGENIOUS",
     "license": "CC BY 4.0 per GDR submission 1391",
     "source_page": "https://gdr.openei.org/submissions/1391",
     "url": "https://gdr.openei.org/files/1391/qfaults_ingenious_nad83conus117_2023-06-27.zip"},
    {"id": "ingenious_paleo", "publisher": "DOE Geothermal Data Repository / INGENIOUS",
     "license": "CC BY 4.0 per GDR submission 1391",
     "source_page": "https://gdr.openei.org/submissions/1391",
     "url": "https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip"},
]


def download(source: dict, cache: Path) -> tuple[bytes, dict]:
    path = cache / f"{source['id']}.zip"
    temporary = path.with_suffix(".partial")
    with requests.get(source["url"], stream=True, timeout=(15, 90),
                      headers={"User-Agent": "GEMSDOE47-authorized-public-data-audit/1.0"}) as response:
        response.raise_for_status()
        if not response.url.startswith("https://") or "/login" in response.url:
            raise ValueError("unsafe or login redirect: public archive not acquired")
        n = 0
        with temporary.open("wb") as stream:
            for chunk in response.iter_content(1 << 20):
                n += len(chunk)
                if n > 50_000_000:
                    raise ValueError("archive exceeds 50 MB feasibility-audit budget")
                stream.write(chunk)
        content = temporary.read_bytes()
        if not zipfile.is_zipfile(io.BytesIO(content)):
            raise ValueError("response is not the declared ZIP archive")
        temporary.replace(path)
        return content, {"http_status": response.status_code, "final_url": response.url,
                         "sha256": hashlib.sha256(content).hexdigest(), "bytes": n}


def coverage(content: bytes, template: G.Template) -> list[dict]:
    rows = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        # Never extract externally-controlled archive paths to the filesystem.
        if sum(e.file_size for e in archive.infolist() if e.filename.lower().endswith((".shp", ".shx", ".prj"))) > 250_000_000:
            raise ValueError("supported shapefile expansion exceeds audit budget")
        names = archive.namelist()
        for name in names:
            if not name.lower().endswith(".shp"):
                continue
            def matching(suffix, name=name):
                found = next((n for n in names if n.lower() == name[:-4].lower() + suffix), None)
                return archive.read(found) if found else None
            prj = matching(".prj")
            if not prj:
                rows.append({"layer": name, "status": "CRS_MISSING_NOT_GUESSED"})
                continue
            src_crs = rasterio.crs.CRS.from_wkt(prj.decode("utf-8-sig"))
            reader = shapefile.Reader(shp=io.BytesIO(archive.read(name)),
                                      dbf=None,  # attributes are unnecessary for geometry-only coverage
                                      shx=io.BytesIO(matching(".shx")) if matching(".shx") else None)
            geoms, geometry_types = [], set()
            west, south, east, north = rasterio.transform.array_bounds(*template.shape, template.transform)
            for shape in reader.iterShapes():
                if shape.shapeType == shapefile.NULL:
                    continue
                g = transform_geom(src_crs, template.crs, shape.__geo_interface__)
                geometry_types.add(g["type"])
                # Rasterize all official features in one pass; GDAL clips to the exact grid.
                geoms.append(g)
            if geoms:
                mask = rasterize(((g, 1) for g in geoms), out_shape=template.shape,
                                 transform=template.transform, all_touched=True, dtype="uint8") > 0
                hits = mask & template.footprint
                count = int(hits.sum())
                known = int((hits & template.catalogue).sum())
                unknown = int((hits & ~template.catalogue).sum())
            else:
                count = known = unknown = 0
            rows.append({"layer": name, "status": "GEOMETRY_RASTERIZED", "source_crs": str(src_crs),
                         "geometry_types": sorted(geometry_types), "features": len(geoms),
                         "rasterization": "all_touched=True, 100m grid; pixel coverage is not truth or a fault count",
                         "pixels_in_template_footprint": count, "pixels_on_supplied_catalogue": known,
                         "pixels_off_exact_catalogue": unknown,
                         "grid_bounds": [west, south, east, north]})
            reader.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "evidence" / "official-download-probes.json")
    args = parser.parse_args()
    template = G.load_template()
    cache = ROOT / ".cache" / "official_probe"
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in SOURCES:
        row = {**source, "attempt_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "used_in_h47c_prediction": False, "hidden_truth_verified": False}
        try:
            content, receipt = download(source, cache)
            row.update(receipt)
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                row["archive_members"] = [{"path": m.filename, "uncompressed_bytes": m.file_size} for m in archive.infolist() if not m.is_dir()][:80]
                row["archive_member_count"] = len(archive.infolist())
            row["layers"] = coverage(content, template)
            row["status"] = ("BYTES_AND_COVERAGE_VERIFIED" if row["layers"] and
                             all(layer["status"] == "GEOMETRY_RASTERIZED" for layer in row["layers"])
                             else "BYTES_VERIFIED_COVERAGE_NOT_VERIFIED")
        except (requests.RequestException, OSError, ValueError, shapefile.ShapefileException,
                rasterio.errors.RasterioError, zipfile.BadZipFile) as error:
            row["status"] = "BYTES_VERIFIED_COVERAGE_NOT_VERIFIED" if "sha256" in row else "NOT_ACQUIRED_OR_NOT_COVERAGE_VERIFIED"
            row["error_type"] = type(error).__name__
            row["error"] = str(error)[:300]
        print(f"{source['id']}: {row['status']}", flush=True)
        rows.append(row)
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sources": rows,
           "all_obtained_and_coverage_checked": all(r["status"] == "BYTES_AND_COVERAGE_VERIFIED" for r in rows),
           "scope": "Official public downloads, feasibility only; no inference features or private labels.",
           "competition_core_inputs_remain_mirrors": True}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    return 0  # failure receipts are data, not permission to pretend bytes are available


if __name__ == "__main__":
    raise SystemExit(main())
