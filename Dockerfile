FROM debian:12.2 as builder

RUN apt-get update && \
    apt-get install -y wget build-essential \
                       libcairo2-dev libnetpbm10-dev netpbm \
                       libpng-dev libjpeg-dev python3-numpy \
                       python3-astropy python3-dev zlib1g-dev \
                       libbz2-dev swig libcfitsio-dev python-is-python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /download
RUN wget http://astrometry.net/downloads/astrometry.net-latest.tar.gz
RUN tar xvzf astrometry.net-latest.tar.gz
RUN cd astrometry.net-* && make && make py && make extra && make install PYTHON_SCRIPT="/usr/bin/python"

FROM debian:12.2-slim
EXPOSE 8000

RUN apt-get update && \
    apt-get install -y python3-numpy python3-astropy python3-flask python3-gunicorn libcfitsio-bin \
                       python-is-python3 && \
    rm -rf /var/lib/apt/lists/* \

WORKDIR /usr/local/
COPY --from=builder /usr/local/astrometry astrometry

WORKDIR /webserver
COPY server.py .
CMD exec gunicorn --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread -b :8000 server:app
