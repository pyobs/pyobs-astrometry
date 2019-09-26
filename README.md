pyobs-astrometry
----------------

A web-service for astrometry.net.

Run as:

    docker run --name astrometry 
               --rm 
               -p 8000:8000 
               -v /usr/local/astrometry/data:/path/to/index/files 
               pyobs-astrometry