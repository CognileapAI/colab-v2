import numpy as np
import json
import os
import subprocess
import sys
from pathlib import Path
from netCDF4 import Dataset
from pyhdf.SD import SD, SDC

from colab_viz.domains.d7_visualization import downsample, readers


def test_windowed_block_average_matches_existing_semantics_without_full_read():
    source = np.arange(63, dtype="f4").reshape(7, 9)
    windows = []

    def read_window(rows, cols):
        windows.append((rows, cols))
        return source[rows, cols]

    got = readers._windowed_block_average(source.shape, (3, 4), read_window)

    np.testing.assert_allclose(got, downsample.block_average(source, (3, 4)))
    assert windows
    assert all((r.stop - r.start) <= 3 for r, _ in windows)
    assert len(windows) == 3
    assert not any(r == slice(None) and c == slice(None) for r, c in windows)


def test_netcdf_downsample_keeps_1d_coordinate_grid(tmp_path):
    path = tmp_path / "grid.nc"
    with Dataset(path, "w") as ds:
        ds.createDimension("lat", 7)
        ds.createDimension("lon", 9)
        ds.createVariable("lat", "f4", ("lat",))[:] = np.linspace(30, 36, 7)
        ds.createVariable("lon", "f4", ("lon",))[:] = np.linspace(120, 128, 9)
        ds.createVariable("rain", "f4", ("lat", "lon"))[:] = np.arange(63).reshape(7, 9)

    field = readers._read_netcdf(path, "rain", None, 3)

    assert field.values.shape == (3, 3)
    assert field.lat is not None and field.lon is not None
    assert field.lat.shape == field.values.shape == field.lon.shape
    assert field.lat[0, 0] == 31 and field.lat[-1, -1] == 36


def test_hdf4_one_row_strip_stays_2d_and_matches_block_average(tmp_path):
    path = tmp_path / "grid.hdf"
    source = np.arange(63, dtype="i2").reshape(7, 9)
    hdf = SD(str(path), SDC.WRITE | SDC.CREATE)
    sds = hdf.create("rain", SDC.INT16, source.shape)
    sds[:] = source
    sds.endaccess()
    hdf.end()

    field = readers._read_hdf4(path, "rain", 3)

    np.testing.assert_allclose(field.values, downsample.block_average(source, (3, 3)))
    assert field.values.shape == (3, 3)


def test_netcdf_2d_coordinates_are_sampled_before_loading(tmp_path):
    path = tmp_path / "coords.nc"
    with Dataset(path, "w") as ds:
        ds.createDimension("y", 7)
        ds.createDimension("x", 9)
        yy, xx = np.meshgrid(np.arange(7), np.arange(9), indexing="ij")
        ds.createVariable("lat", "f4", ("y", "x"))[:] = 30 + yy
        ds.createVariable("lon", "f4", ("y", "x"))[:] = 120 + xx
        ds.createVariable("rain", "f4", ("y", "x"))[:] = yy * 9 + xx

    field = readers._read_netcdf(path, "rain", None, 3)

    assert field.lat.shape == field.values.shape == (3, 3)
    assert field.lon.shape == (3, 3)
    assert field.lat[-1, -1] == 36 and field.lon[-1, -1] == 128


def test_projection_coordinates_are_created_at_preview_shape(tmp_path, monkeypatch):
    path = tmp_path / "projected.nc"
    with Dataset(path, "w") as ds:
        ds.createDimension("y", 7)
        ds.createDimension("x", 9)
        ds.createVariable("rain", "f4", ("y", "x"))[:] = np.arange(63).reshape(7, 9)
        mapping = ds.createVariable("projection", "i1")
        mapping.grid_mapping_name = "lambert_conformal_conic"
        mapping.standard_parallel1 = 30.0
        mapping.standard_parallel2 = 60.0
        mapping.origin_latitude = 38.0
        mapping.central_meridian = 126.0
        mapping.upper_left_easting = -4000.0
        mapping.upper_left_northing = 3000.0
        mapping.pixel_size = 1000.0
    seen = []
    monkeypatch.setattr(readers.coords, "_to_lonlat",
                        lambda _p, xs, ys: (seen.append(xs.shape) or (ys, xs)))

    field = readers._read_netcdf(path, "rain", None, 3)

    assert field.lat.shape == field.values.shape == (3, 3)
    assert seen == [(3, 3)]


def test_hdf_struct_coordinates_are_created_at_preview_shape(monkeypatch):
    text = """
XDim=9 YDim=7
UpperLeftPointMtrs=(-4000.0,3000.0)
LowerRightMtrs=(5000.0,-4000.0)
ProjParams=(6371007.181,0,0)
GCTP_SNSOID
"""
    seen = []
    monkeypatch.setattr(readers.coords, "_to_lonlat",
                        lambda _p, xs, ys: (seen.append(xs.shape) or (ys, xs)))

    lat, lon = readers.coords.from_struct_metadata(
        text, row_indices=np.array([1, 4, 6]), col_indices=np.array([1, 5, 8]))

    assert lat.shape == lon.shape == (3, 3)
    assert seen == [(3, 3)]


def test_real_netcdf_reader_peak_rss_stays_bounded_by_preview_size(tmp_path):
    path = tmp_path / "large.nc"
    with Dataset(path, "w") as ds:
        ds.createDimension("y", 3000)
        ds.createDimension("x", 3000)
        var = ds.createVariable("rain", "i2", ("y", "x"))
        row = np.arange(3000, dtype="i2")
        var[:, :] = np.broadcast_to(row, (3000, 3000))

    script = """
import json, resource, sys
from pathlib import Path
from colab_viz.domains.d7_visualization.readers import _read_netcdf
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
field = _read_netcdf(Path(sys.argv[1]), 'rain', None, 100)
print(json.dumps({'shape': field.values.shape, 'beforeKiB': before,
                  'rssKiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run([sys.executable, "-c", script, str(path)], check=True,
                            text=True, capture_output=True, env=env)
    measured = json.loads(result.stdout)

    assert measured["shape"] == [100, 100]
    assert measured["rssKiB"] - measured["beforeKiB"] < 120 * 1024


def test_real_hdf4_reader_peak_rss_stays_bounded_by_preview_size(tmp_path):
    path = tmp_path / "large.hdf"
    hdf = SD(str(path), SDC.WRITE | SDC.CREATE)
    sds = hdf.create("rain", SDC.INT16, (3000, 3000))
    row = np.arange(3000, dtype="i2")
    sds[:, :] = np.broadcast_to(row, (3000, 3000))
    sds.endaccess()
    hdf.end()
    script = """
import json, resource, sys
from pathlib import Path
from colab_viz.domains.d7_visualization.readers import _read_hdf4
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
field = _read_hdf4(Path(sys.argv[1]), 'rain', 100)
print(json.dumps({'shape': field.values.shape, 'beforeKiB': before,
                  'rssKiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run([sys.executable, "-c", script, str(path)], check=True,
                            text=True, capture_output=True, env=env)
    measured = json.loads(result.stdout)

    assert measured["shape"] == [100, 100]
    assert measured["rssKiB"] - measured["beforeKiB"] < 120 * 1024
