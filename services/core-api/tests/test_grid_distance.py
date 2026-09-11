"""J-3: 경계가 같아도 화소 크기 차이가 있으면 거리 비교에 포함한다."""
from colab_core.app.routes.ingestion import _corner_distance_meters


def test_same_extent_with_different_pixel_size_has_nonzero_distance():
    left = dict(west=126, south=34, east=130, north=38, grid_shape=[4, 4])
    right = dict(left, grid_shape=[8, 8])
    assert _corner_distance_meters(left, right) > 0
    assert _corner_distance_meters(left, left) == 0


def test_missing_pixel_shape_is_unknown():
    left = dict(west=126, south=34, east=130, north=38, grid_shape=[4, 4])
    assert _corner_distance_meters(left, dict(left, grid_shape=None)) is None
