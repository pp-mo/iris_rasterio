# Module interfacing Iris to Rasterio
# Exchange cubes <--> rasterio for loading + saving
import iris
import rasterio

import numpy as np


class RasterioContent(object):
    """
    A generic 2d raster object.

    Can be generated from a cube and then saved to various file formats
    supported by rasterio.

    """
    def __init__(self, cube):
        self._cube = cube
        # Grab things we need to check that they exist.
        if cube.ndim != 2:
            raise ValueError('Cube is not 2d:\n{}'.format(cube))
        self._x_coord = cube.coord(axis='x', dim_coords=True)
        self._y_coord = cube.coord(axis='y', dim_coords=True)
        self._coord_system = cube.coord_system()
        self._calc_done = False

    def _calc(self):
        if self._calc_done:
            return
        nx, = self._x_coord.shape
        self._width = nx
        ny, = self._y_coord.shape
        self._height = ny
        crs = self._coord_system.as_cartopy_crs()
        proj4_dict = crs.proj4_params
        self._rasterio_crs = proj4_dict

        # Work out the dtype we shall be using.
        # For some tiresome reason, we must translate numpy dtypes
        # into "rasterio dtypes".
        # At present we are also making it recast any float data as float32,
        # because float64 did not work somehow?
        dtype = self._cube.dtype
        self._output_dtype = dtype
        if dtype.kind == 'f':
            self._output_dtype = np.float32
            dtype = rasterio.float32
        elif dtype.kind == 'i':
            if dtype.itemsize == 1:
                dtype = rasterio.int8
            else:
                dtype = rasterio.int16
        elif dtype.kind == 'u':
            if dtype.itemsize == 1:
                dtype = rasterio.uint8
            else:
                dtype = rasterio.uint16
        self._rasterio_dtype = dtype

    @property
    def width(self):
        self._calc()
        return self._width

    @property
    def height(self):
        self._calc()
        return self._height

    @property
    def rasterio_crs(self):
        self._calc()
        return self._rasterio_crs

    @property
    def rasterio_dtype(self):
        self._calc()
        return self._rasterio_dtype

    @property
    def data(self):
        data = self._cube.data
        data = data.astype(self._output_dtype)
        return data

    def save(self, file_path, rasterio_driver='GTiff'):
        """
        Save to file with rasterio.

        Default filetype is geotiff.

        """

        # Hacky bit to correct crs parameters.
        crs = raster.rasterio_crs
        if crs.get('proj') == 'lonlat':
            print 'Save : original crs was = ', crs
            crs['proj'] = 'longlat'  # ??RENAME
            print 'Save : using modified crs = ', crs

        with rasterio.open(path=file_path, mode='w', driver=rasterio_driver,
                           width=raster.width, height=raster.height,
                           count=1,
                           crs=crs,
                           dtype=raster.rasterio_dtype) as dataset:
            dataset.write(raster.data, 1)


def file_report(file_path):
    # Suck it back in
    readback = rasterio.open(file_path)
    data = readback.read(1)
    print 'readback:'
    print '  crs=', readback.crs
    print '  width=', readback.width
    print '  height=', readback.height
    print '  data-shape=', data.shape
    print '  data-dtype=', data.dtype
    print '  data-min=', np.min(data)
    print '  data-max=', np.max(data)


if __name__ == '__main__':
    import iris.tests.stock as istk
    test_cube = istk.global_pp()

    print 'Original float file version:'
    raster = RasterioContent(test_cube)
    raster.save('tmp1.tif')
    file_report('tmp1.tif')

    # Let's rescale to 0..255, just for fun
    datamin = np.min(test_cube.data)
    datamax = np.max(test_cube.data)
    newmin = 25.
    newmax = 215.
    ratio = (newmax - newmin) / (datamax - datamin)
    test_cube.data = newmin + ratio * (test_cube.data - datamin)
    # Let's also make it into bytes
    test_cube.data = test_cube.data.astype(np.uint8)

    print
    print 'Modified 8-bit file version:'
    raster = RasterioContent(test_cube)
    raster.save('tmp2.tif')
    file_report('tmp2.tif')

