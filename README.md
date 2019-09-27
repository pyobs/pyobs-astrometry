# pyobs-astrometry

A web-service for astrometry.net.

Inspired by LCO's Banzai pipeline:
https://github.com/LCOGT/banzai

## Deploy

Build image:

    docker build . -t pyobs-astrometry

Run as:

    docker run --name astrometry 
               --rm 
               -p 8000:8000 
               -v /path/to/index/files:/usr/local/astrometry/data 
               pyobs-astrometry
               
## Usage

The web-service accepts a POST request (to port 8000 in the example above) with a JSON payload 
like this:

    {
        ra: <ra>,
        dec: <dec>,
        scale_low: <scale_low>,
        scale_high: <scale_high>,
        nx: <width>,
        ny: <height>,
        x: <x list>,
        y: <y list>,
        flux: <flux list>
    }
    
Where ra and dec are first guess coordinates, scale_low and _high define the expected plate scale in 
arcsec/px, and nx/ny are the size of the whole image. Finally, x, y, and flux, are lists of coordinates
and fluxes for all found stars in the field.

The response is a dictionary containing either an "error" field, or all FITS headers that should
be set in the original FITS file.