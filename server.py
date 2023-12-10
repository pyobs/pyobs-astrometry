import os
import shlex
import subprocess
import tempfile
from astropy.io import fits
from astropy.io.fits import table_to_hdu
from flask import Flask, request, Response
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
import json
import logging


# flask app
app = Flask(__name__)

# logger
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s', level=logging.INFO)


@app.route('/', methods=['POST'])
def astrometry():

    # get JSON
    data = request.get_json()
    logging.info('New request: %s', data)

    # check request
    if 'ra' not in data or 'dec' not in data:
        raise ValueError('Either RA or Dec not found in request.')
    if 'scale_low' not in data or 'scale_high' not in data or data['scale_low'] > data['scale_high']:
        raise ValueError('Invalid scales given.')
    if 'nx' not in data or 'ny' not in data or data['nx'] <= 0 or data['ny'] <= 0:
        raise ValueError('Invalid image size given.')

    # coordinates and radius
    ra = data['ra']
    dec = data['dec']
    radius = data['radius'] if 'radius' in data else 3.
    coords = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
    logging.info('Searching within radius of %.2g degrees around %s.', radius, str(coords))

    # get scale and image size
    scale_low = data['scale_low']
    scale_high = data['scale_high']
    logging.info('Scale is given as %.2g <= scale <= %.2g.', scale_low, scale_high)
    nx = data['nx']
    ny = data['ny']
    logging.info('Image size is %dx%d.', nx, ny)

    # get x and y coordinates and fluxes of sources
    x = data['x']
    y = data['y']
    flux = data['flux']
    logging.info('Found %d sources.', len(x))

    # define command
    cmd = f"--crpix-center --no-verify --no-tweak " \
          f" --radius {radius} --ra {ra} --dec {dec} --guess-scale " \
          f"--scale-units arcsecperpix --scale-low {scale_low} --scale-high {scale_high} " \
          f"--no-plots -N none --no-remove-lines " \
          f"--code-tolerance 0.003 --pixel-error 1 -d 1-200 " \
          f"--solved none --match none --rdls none --wcs wcs.fits --corr none --overwrite " \
          f"-X X -Y Y -s FLUX --width {nx} --height {ny}"

    # crpix?
    if 'crpix-x' in data and 'crpix-y' in data:
        cmd += f" --crpix-x {data['crpix-x']} --crpix-y {data['crpix-y']}"

    # add catalog
    cmd += " cat.fits"
    logging.info(cmd)

    # solve-field executable and library path
    exec = '/usr/local/astrometry/bin/solve-field'
    path = '/usr/local/astrometry/lib/python'

    # create table
    tbl = Table([x, y, flux], names=('x', 'y', 'flux'))

    # create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write catalog
        table_to_hdu(tbl).writeto(os.path.join(tmpdir, 'cat.fits'))

        # run astrometry.net
        try:
            out = subprocess.check_output([exec] + shlex.split(cmd), cwd=tmpdir, env={'PYTHONPATH': path})
            logging.info('astrometry.net log:')
            for line in out.decode('utf-8').split('\n'):
                logging.info(line)
        except subprocess.CalledProcessError as e:
            raise ValueError('Astrometry.net threw an error: ' + e.output)

        # WCS file exists?
        if not os.path.exists(os.path.join(tmpdir, 'wcs.fits')):
            raise ValueError('Could not find WCS file.')

        # open WCS file
        wcs_header = fits.getheader(os.path.join(tmpdir, 'wcs.fits'))

        # copy keywords
        keywords = ['CTYPE1', 'CTYPE2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2']
        header = {k: wcs_header[k] for k in keywords}

        # log
        coords = SkyCoord(ra=wcs_header['CRVAL1'] * u.deg, dec=wcs_header['CRVAL2'] * u.deg, frame='icrs')
        logging.info('Found coordinates %s.', str(coords))

    # define response
    response = Response(json.dumps(header))
    response.content_type = 'application/json'
    logging.info('Finished.')
    return response


@app.errorhandler(Exception)
def handle_error(error):
    logging.error('An exception has occured: %s', str(error))
    response = Response()
    response.data = json.dumps({'error': str(error)})
    response.content_type = 'application/json'
    response.status_code = 400
    return response
