pyobs-astrometry
################

A web service wrapping `astrometry.net <http://astrometry.net/>`_'s ``solve-field`` plate solver:
POST a first-guess pointing plus a source list, get back the WCS FITS headers to plate-solve the
original image. Inspired by LCO's `Banzai pipeline <https://github.com/LCOGT/banzai>`_.

Unlike the rest of the pyobs-core fleet, this is a single Flask endpoint in one file
(``server.py``) with no persistent state, no database, and no Python dependency management (apt
packages inside the Docker image, not a ``pyproject.toml``/``uv.lock``) — one page covers it,
there's nothing to split into installation/configuration/architecture pages.


Deploy
******

Build the image (compiles astrometry.net from source — takes a while)::

    docker build . -t pyobs-astrometry

astrometry.net needs index files to match against, which aren't bundled in the image — download
the ones covering your expected field sizes from `astrometry.net's index file page
<http://data.astrometry.net/>`_ and mount them read-only at
``/usr/local/astrometry/data``::

    docker run --name astrometry \
               --rm \
               -p 8000:8000 \
               -v /path/to/index/files:/usr/local/astrometry/data \
               pyobs-astrometry

Served by gunicorn (2 workers, 4 threads each, ``gthread`` worker class — see the ``Dockerfile``'s
``CMD``) on port 8000.


Usage
*****

``POST /`` with a JSON payload::

    {
        "ra": <ra>,
        "dec": <dec>,
        "scale_low": <scale_low>,
        "scale_high": <scale_high>,
        "nx": <width>,
        "ny": <height>,
        "x": <x list>,
        "y": <y list>,
        "flux": <flux list>
    }

- ``ra``/``dec`` — first-guess pointing, in degrees.
- ``radius`` (optional, default ``3.0``) — search radius around ``ra``/``dec``, in degrees.
- ``scale_low``/``scale_high`` — expected plate scale range, in arcsec/px.
- ``nx``/``ny`` — full image size in pixels.
- ``x``/``y``/``flux`` — pixel coordinates and flux of each detected source in the field.
- ``crpix-x``/``crpix-y`` (optional) — fix the reference pixel instead of letting
  ``solve-field`` choose it (``--crpix-x``/``--crpix-y``).

The response is either ``{"error": "<message>"}`` (HTTP 400) or the ten WCS FITS keywords
(``CTYPE1``, ``CTYPE2``, ``CRPIX1``, ``CRPIX2``, ``CRVAL1``, ``CRVAL2``, ``CD1_1``, ``CD1_2``,
``CD2_1``, ``CD2_2``) to merge into the original FITS header.
