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


def send_error(error):
    """Return JSON instead of HTML for HTTP errors."""
    print("handler")
    response = Response()
    response.data = json.dumps({'error': error})
    response.content_type = 'application/json'
    response.status_code = 400
    return response


@app.route('/', methods=['POST'])
def astrometry():
    # get JSON
    data = request.get_json()

    # check request
    if 'ra' not in data or 'dec' not in data:
        return send_error('Either RA or Dec not found in request.')

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

    # solve-field executable
    exec = '/usr/local/astrometry/bin/solve-field'
    path = os.path.abspath(os.path.join(exec, '../../lib/python'))

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
            return send_error('Astrometry.net threw an error.')

        # WCS file exists?
        if not os.path.exists(os.path.join(tmpdir, 'wcs.fits')):
            return send_error('Could not find WCS file.')

        # open WCS file
        wcs_header = fits.getheader(os.path.join(tmpdir, 'wcs.fits'))

        # copy keywords
        keywords = ['CTYPE1', 'CTYPE2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2']
        header = {k: wcs_header[k] for k in keywords}

    # define response
    response = Response(json.dumps(header))
    response.content_type = 'application/json'
    return response
