"""Run selected real-file browser journeys against one disposable stack.

Cases are fixed inputs. COLAB_UI_CASES selects a comma-separated subset.
Each case keeps its own screenshots, original hash and downloaded byte proof.
"""
import copy
import importlib.util
import os
from pathlib import Path


def run(command, args, session):
    root = Path(os.environ['COLAB_REFERENCE_DATA'])
    formats = root / '02.File-format'
    veg = root / '01.level-data/02.vegetation/02.vegetation'
    cases = {
        'hdf': (formats / 'file_format_5_HDF5/00.Data/MOD15A2H.A2019273.h27v05.061.2020313082826.hdf', [], True, False),
        'contract': (formats / 'file_format_5_HDF5/00.Data/MOD15A2H.A2019273.h27v05.061.2020313082826.hdf', [], True, False),
        'nc': (formats / 'file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_202005010000.nc', [], False, False),
        'grib': (formats / 'file_format_1_grib/00.Data/surface.grib', [], False, True),
        'bin': (formats / 'file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_202508131000.bin.gz', [], False, False),
        'bin-grid': (formats / 'file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_202508131000.bin.gz', [formats / 'file_format_3_bin/04.Lat_Lon_info/rdr_500m_latlon.nc'], False, False),
        'partial': (formats / 'file_format_4_tif/00.Data/HLS.S30.T51SYB.2025359T023019.v2.0.B02.tif', [], False, False),
    }
    selected = os.environ.get('COLAB_UI_CASES', 'hdf,nc,grib,bin,bin-grid').split(',')
    if 'numpy' in selected:
        cases['numpy'] = (sorted((veg / 'Lv.2').glob('Prediction_*.npy'))[0], [veg / '#metadata/LAT_crop.npy', veg / '#metadata/LON_crop.npy'], False, False)
    spec = importlib.util.spec_from_file_location('upload_journey', Path(__file__).with_name('upload-preview-journey.py'))
    journey = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(journey)
    for key in selected:
        source, grids, connections, unsupported = cases[key]
        case = copy.copy(args)
        case.upload_file, case.grid_file, case.extra_file = source, grids, []
        if key == 'partial':
            broken = args.artifacts / 'inputs/intentional-unreadable.tif'
            broken.parent.mkdir(parents=True, exist_ok=True)
            broken.write_bytes(b'Intentional invalid TIFF for partial failure verification\n')
            case.extra_file = [broken]
            case.expect_partial = True
        case.connections, case.expect_unsupported = connections, unsupported
        case.contract_expansion = key == 'contract'
        case.artifacts = args.artifacts / key
        print('CASE:', key, flush=True)
        journey.run(command, case, session + '-' + key)
