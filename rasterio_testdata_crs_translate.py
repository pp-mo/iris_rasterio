import rasterio
import os
import os.path

from glob import glob

def recognise_crs_epsgcode(params):
    result = None
    init_str = params.get('init')
    if init_str and init_str[:5] == 'epsg:':
        try:
            result = int(init_str[5:])
        except ValueError:
            pass
    return result

import pyepsg

def translate_epsgcode(code_number):
    pyepsg_crs = pyepsg.get(code_number)
    return pyepsg_crs.as_proj4()

basedir_path = os.path.dirname(__file__)
testfiles_spec = os.sep.join([basedir_path, 'test_data', '*.tif'])
file_paths = glob(testfiles_spec)


for file_path in file_paths:
    data = rasterio.open(file_path)
    crs = data.crs
    code = recognise_crs_epsgcode(crs)
    if code is not None:
        print '{}\n  : crs={}'.format(
            os.path.basename(file_path),
            crs)
        print '   epsg=', code
        proj4_generic_params = translate_epsgcode(code)
        print '   proj4=', proj4_generic_params

