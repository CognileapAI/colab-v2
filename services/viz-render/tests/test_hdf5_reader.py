from pathlib import Path

import h5py
import numpy as np
import pytest

from colab_viz.domains.d7_visualization.failures import NotRenderableError
from colab_viz.domains.d7_visualization.readers import (
    FieldReadError,
    SUPPORTED_FORMATS,
    describe_field,
    read_field,
)


def _fixture(path: Path) -> Path:
    with h5py.File(path, "w") as h5:
        a = h5.create_dataset("group/value", data=np.array([
            [[-9999, 1], [2, 3]], [[4, 5], [6, 7]]], dtype="i2"))
        a.attrs["_FillValue"] = -9999
        a.attrs["scale_factor"] = 0.5
        a.attrs["add_offset"] = 10.0
        a.attrs["units"] = "K"
        h5.create_dataset("other/value", data=np.ones((2, 2), dtype="f4"))
        h5.create_dataset("label", data=np.array([b"a", b"b"]))
    return path


def test_hdf5_lists_full_dataset_paths_and_explicit_slices(tmp_path: Path):
    path = _fixture(tmp_path / "ordinary.h5")
    fmt, variables, instants = describe_field(path)
    assert fmt == "HDF5" and instants == []
    assert variables == ["hdf5:/group/value[0]", "hdf5:/group/value[1]", "hdf5:/other/value"]
    assert "HDF5" in SUPPORTED_FORMATS


def test_hdf5_masks_raw_fill_before_scale_and_has_no_invented_coordinates(tmp_path: Path):
    path = _fixture(tmp_path / "ordinary.h5")
    fmt, field = read_field(path, variable="hdf5:/group/value[0]")
    assert fmt == "HDF5"
    assert np.isnan(field.values[0, 0])
    assert field.values[0, 1] == pytest.approx(10.5)
    assert field.unit == "K"
    assert field.has_position is False


def test_hdf5_rejects_bad_selection_and_string_only_file(tmp_path: Path):
    path = _fixture(tmp_path / "ordinary.h5")
    with pytest.raises(FieldReadError):
        read_field(path, variable="hdf5:/group/value[4]")
    strings = tmp_path / "strings.h5"
    with h5py.File(strings, "w") as h5:
        h5.create_dataset("names", data=np.array([b"a", b"b"]))
    with pytest.raises(NotRenderableError):
        describe_field(strings)


def test_hdf5_uses_only_same_group_coordinates(tmp_path: Path):
    path = tmp_path / "coords.h5"
    with h5py.File(path, "w") as h5:
        science = h5.create_group("science")
        science.create_dataset("value", data=np.ones((2, 2)))
        wrong = h5.create_group("wrong")
        wrong.create_dataset("lat", data=np.full((2, 2), 35.0))
        wrong.create_dataset("lon", data=np.full((2, 2), 127.0))
    _, field = read_field(path, variable="hdf5:/science/value")
    assert field.has_position is False

    with h5py.File(path, "a") as h5:
        h5["science"].create_dataset("lat", data=np.full((2, 2), 36.0))
        h5["science"].create_dataset("lon", data=np.full((2, 2), 128.0))
    _, field = read_field(path, variable="hdf5:/science/value")
    assert field.has_position is True
    assert np.all(field.lat == 36.0) and np.all(field.lon == 128.0)


def test_hdf5_escapes_brackets_in_dataset_paths_and_excludes_complex(tmp_path: Path):
    path = tmp_path / "names.h5"
    with h5py.File(path, "w") as h5:
        h5.create_dataset("a[0]", data=np.ones((2, 2)))
        h5.create_dataset("complex", data=np.ones((2, 2), dtype="c8"))
    _, variables, _ = describe_field(path)
    assert variables == ["hdf5:/a%5B0%5D"]
    _, field = read_field(path, variable=variables[0])
    assert field.values.shape == (2, 2)


def test_hdf5_refuses_unbounded_slice_enumeration(tmp_path: Path):
    path = tmp_path / "huge.h5"
    with h5py.File(path, "w") as h5:
        h5.create_dataset("value", shape=(4097, 2, 2), dtype="f4")
    with pytest.raises(NotRenderableError, match="목록 상한"):
        describe_field(path)


def test_hdf5_ambiguous_same_group_coordinates_stay_non_map(tmp_path: Path):
    path = tmp_path / "ambiguous.h5"
    with h5py.File(path, "w") as h5:
        h5.create_dataset("value", data=np.ones((2, 2)))
        for name, value in (("lat", 35), ("latitude", 36), ("lon", 127), ("longitude", 128)):
            h5.create_dataset(name, data=np.full((2, 2), value))
    _, field = read_field(path, variable="hdf5:/value")
    assert field.has_position is False
