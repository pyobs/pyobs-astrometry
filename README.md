# pyobs-astrometry

A web-service for astrometry.net.

Inspired by LCO's Banzai pipeline:
https://github.com/LCOGT/banzai

## Documentation

Full deploy (including where to get astrometry.net's index files) and usage (the request/response
JSON shape): see [`docs/source/index.rst`](docs/source/index.rst) (built with Sphinx —
`cd docs && uv run --with sphinx --with sphinx-rtd-theme make html`).

## Deploy

Build image:

    docker build . -t pyobs-astrometry

Run as:

    docker run --name astrometry 
               --rm 
               -p 8000:8000 
               -v /path/to/index/files:/usr/local/astrometry/data 
               pyobs-astrometry
