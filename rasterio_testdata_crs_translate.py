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

#import pyepsg
#
#def translate_epsgcode(code_number):
#    pyepsg_crs = pyepsg.get(code_number)
#    return pyepsg_crs.as_proj4()


basedir_path = os.path.dirname(__file__)
testfiles_spec = os.sep.join([basedir_path, 'test_data', '*.tif'])
file_paths = glob(testfiles_spec)


_epsg_translations = {}

import pyproj
import re
epsg_line_re = re.compile('^ *<(?P<epsgcode>[0-9]*)>(?P<proj4params>.*)')

def _ensure_epsg_translations():
    if _epsg_translations:
        return

    # This is the nasty hacky bit .
    # Pull the epsg definitions file out of Proj4, as it is not exposed...
    basedir_path = os.path.dirname(pyproj.__file__)
    codesfile_path = os.sep.join([
        basedir_path, 'data', 'epsg'])
    # ...then massage that into a database of known translations from the
    # "init=epsg:xxx" form to more "generic" proj4 parameter descriptions.
    #
    # BECAUSE: this will allow us to translate the CRS from incoming files
    # into Iris
    # coordinate systems.
    #
    with open(codesfile_path) as infile:
        for line in infile.readlines():
            match = epsg_line_re.match(line)
            if match:
                code = match.group('epsgcode')
                try:
                    code = int(code)
                except ValueError:
                    msg = 'Failed to translate Epsg code {} to integer.'
                    raise ValueError(msg.format(code))
                params = match.group('proj4params')
                param_parts = params.strip().split(' ')
                param_parts = [s[1:] for s in param_parts
                               if len(s) and s[:1] == '+']
                param_dict = dict()
                for param in param_parts:
                    param_bits = [s.strip() for s in param.split('=')]
                    n_bits = len(param_bits)
                    if n_bits == 1:
                        param_dict[param_bits[0]] = None
                    elif n_bits == 2:
                        param_dict[param_bits[0]] = param_bits[1]
                    else:
                        msg = 'Proj4 param not understood : {}'
                        raise ValueError(msg.format(param))
                _epsg_translations[code] = param_dict


def translate_epsgcode(code_number):
    _ensure_epsg_translations()
    return _epsg_translations[code_number]


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

