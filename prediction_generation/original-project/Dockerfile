FROM ubuntu:20.04

RUN apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
	apt-get remove -y python && \
	apt-get install -y --no-install-recommends \
        wget \
        software-properties-common \
		git \
		build-essential \
		r-base \
		r-base-dev \
		r-cran-rcppeigen \
		latexmk \
		texlive-latex-extra \
		libopenmpi-dev \
		liblzma-dev \
		libgit2-dev \
		libxml2-dev \
		libcurl4-openssl-dev \
		libssl-dev \
		libopenblas-dev \
		libfreetype6-dev \
		libv8-dev

RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y --no-install-recommends \
	python3.9 \
	python3.9-dev \
	python3.9-tk \
	python3.9-distutils \
    python3.9-venv \
    python3-pip && \
    python3.9 -m pip install --no-cache-dir --upgrade setuptools && \
    python3.9 -m pip install virtualenv abed wheel jsonschema

# Set the default shell to bash, needed to run abed_conf.py source commands
RUN mv /bin/sh /bin/sh.old && cp /bin/bash /bin/sh

# Clone the repo and init venvs
RUN git clone https://github.com/simontrapp/TCPDBench && cd /TCPDBench && make venvs
# create empty directories for results
RUN mkdir -p /TCPDBench/analysis/output/summaries && mkdir -p /TCPDBench/abed_results
# Install Python dependencies
RUN python3.9 -m pip install -r /TCPDBench/analysis/requirements.txt
