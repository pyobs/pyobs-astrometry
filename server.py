import os
import shlex
import subprocess
import tempfile
from astropy.io import fits
from astropy.io.fits import table_to_hdu
from flask import Flask, escape, request, Response
from astropy.table import Table
import json


app = Flask(__name__)


@app.route('/', methods=['POST'])
def astrometry():
    # get JSON
    data = request.get_json()

    # check request
    if 'ra' not in data or 'dec' not in data:
        raise ValueError('Either RA or Dec not found in request.')
    if 'scale_low' not in data or 'scale_high' not in data or data['scale_low'] > data['scale_high']:
        raise ValueError('Invalid scales given.')
    if 'nx' not in data or 'ny' not in data or data['nx'] <= 0 or data['ny'] <= 0:
        raise ValueError('Invalid image size given.')

    # define command
    cmd = '--crpix-center --no-verify --no-tweak ' \
          ' --radius 2.0 --ra {ra} --dec {dec} --guess-scale ' \
          '--scale-units arcsecperpix --scale-low {scale_low} --scale-high {scale_high} ' \
          '--no-plots -N none --no-remove-lines ' \
          '--code-tolerance 0.003 --pixel-error 1 -d 1-200 ' \
          '--solved none --match none --rdls none --wcs wcs.fits --corr none --overwrite ' \
          '-X X -Y Y -s FLUX --width {nx} --height {ny} cat.fits'

    # and format it
    command = cmd.format(ra=data['ra'], dec=data['dec'], scale_low=data['scale_low'], scale_high=data['scale_high'],
                         nx=data['nx'], ny=data['ny'])

    # solve-field executable and library path
    exec = '/usr/local/astrometry/bin/solve-field'
    path = '/usr/local/astrometry/lib/python'

    # create table
    tbl = Table([data['x'], data['y'], data['flux']], names=('x', 'y', 'flux'))

    # create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write catalog
        table_to_hdu(tbl).writeto(os.path.join(tmpdir, 'cat.fits'))

        # run astrometry.net
        try:
            subprocess.check_output([exec] + shlex.split(command), cwd=tmpdir, env={'PYTHONPATH': path})
        except subprocess.CalledProcessError:
            raise ValueError('Astrometry.net threw an error.')

        # WCS file exists?
        if not os.path.exists(os.path.join(tmpdir, 'wcs.fits')):
            raise ValueError('Could not find WCS file.')

        # open WCS file
        wcs_header = fits.getheader(os.path.join(tmpdir, 'wcs.fits'))

        # copy keywords
        keywords = ['CTYPE1', 'CTYPE2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2']
        header = {k: wcs_header[k] for k in keywords}

    # define response
    response = Response(json.dumps(header))
    response.content_type = 'application/json'
    return response


@app.errorhandler(Exception)
def handle_error(error):
    response = Response()
    response.data = json.dumps({'error': str(error)})
    response.content_type = 'application/json'
    response.status_code = 400
    return response
