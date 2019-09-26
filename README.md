pyobs-astrometry
----------------

A web-service for astrometry.net.

Build image:

    docker build . -t pyobs-astrometry

Run as:

    docker run --name astrometry 
               --rm 
               -p 8000:8000 
               -v /path/to/index/files:/usr/local/astrometry/data 
               pyobs-astrometry
               
