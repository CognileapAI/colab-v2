"""Serialize access to netCDF-C's process-global native state.

Describe requests and render workers share a process. Separate Dataset handles
do not make netCDF-C thread safe. Reentrancy is needed because describe detects
the file format before opening it again. Raster rendering stays outside this lock.
"""
from functools import wraps
from threading import RLock
from typing import Callable, ParamSpec, TypeVar

_lock = RLock()
P = ParamSpec('P')
T = TypeVar('T')


def serialized_netcdf(function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> T:
        with _lock:
            return function(*args, **kwargs)
    return guarded
