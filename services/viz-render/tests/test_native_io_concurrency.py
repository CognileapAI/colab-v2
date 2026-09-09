"""The HTTP describe route and render jobs read native files concurrently.

Run in a child process so a native crash fails this test without killing pytest.
"""
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_parallel_describe_render_and_reference_grid_keep_process_and_values(tmp_path):
    code = textwrap.dedent('''
        import resource, sys
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        from pathlib import Path
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        import numpy as np
        from netCDF4 import Dataset
        from colab_viz.domains.d7_visualization.readers import read_field, describe_field, detect_format
        from colab_viz.domains.d7_visualization.grid import _from_netcdf
        path = Path(sys.argv[1]) / 'concurrent.nc'
        with Dataset(path, 'w') as ds:
            ds.createDimension('y', 16)
            ds.createDimension('x', 16)
            ds.createVariable('rain', 'f4', ('y', 'x'))[:] = np.full((16, 16), 7)
            ds.createVariable('lat', 'f4', ('y', 'x'))[:] = np.full((16, 16), 37)
            ds.createVariable('lon', 'f4', ('y', 'x'))[:] = np.full((16, 16), 127)
        barrier = Barrier(4)
        def read(kind):
            barrier.wait()
            for _ in range(20):
                if kind == 0:
                    assert detect_format(path) == 'NetCDF'
                elif kind == 1:
                    assert 'rain' in describe_field(path)[1]
                elif kind == 2:
                    fmt, field = read_field(path)
                    assert fmt == 'NetCDF' and np.all(field.values == 7)
                else:
                    grid = _from_netcdf(path)
                    assert np.all(grid.lat == 37) and np.all(grid.lon == 127)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(read, range(4)))
        print('80 native reads verified')
    ''')
    result = subprocess.run([sys.executable, '-X', 'faulthandler', '-c', code, str(tmp_path)],
                            text=True, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stderr[-5000:]
    assert '80 native reads verified' in result.stdout
