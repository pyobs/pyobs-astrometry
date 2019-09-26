FROM debian:10.0 as builder
RUN apt-get update
RUN apt-get install -y wget build-essential \
                       libcairo2-dev libnetpbm10-dev netpbm \
                       libpng-dev libjpeg-dev python3-numpy \
                       python3-astropy python3-dev zlib1g-dev \
                       libbz2-dev swig libcfitsio-dev
RUN ln -s /usr/bin/python3 /usr/bin/python
WORKDIR /download
RUN wget http://astrometry.net/downloads/astrometry.net-latest.tar.gz
RUN tar xvzf astrometry.net-latest.tar.gz
RUN cd astrometry.net-* && make && make py && make extra && make install PYTHON_SCRIPT="/usr/local/bin/python"

FROM python:3.7-slim
EXPOSE 8000
RUN apt-get update \
  && apt-get install -y libcfitsio-bin \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/local/
COPY --from=builder /usr/local/astrometry astrometry
WORKDIR /webserver
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
CMD exec gunicorn --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread -b :8000 server:app
