# ===========================
# STAGE 1: Build PyTorch environment
# ===========================
FROM python:3.9-slim as pytorch-stage

WORKDIR /venv-stage

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev curl

# Create isolated virtual environment for PyTorch
RUN python3 -m venv /venv_pytorch
COPY prediction_generation/requirements-pytorch.txt requirements.txt

# Install PyTorch and alibi-detect
RUN /bin/bash -c "source /venv_pytorch/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt"

# ===========================
# STAGE 2: Main TCPDBench image
# ===========================
FROM simoneismann/tcpdbench:latest

ENV PROJECT_FOLDER='prediction_generation'
ARG ANNOTATIONS_PATH='annotations.json'
ARG DATASETS_PATH='datasets'
ARG SIG_ATTIBUTES='signatures_attributes.json'

WORKDIR /TCPDBench

# System packages
RUN apt-get update && apt-get install -y \
    nano python3.9-distutils python3.9-dev \
    build-essential python3-distutils python3-setuptools curl

# Create main virtual environment
RUN python3.9 -m venv /TCPDBench/execs/python/venv
COPY ${PROJECT_FOLDER}/requirements-venv.txt /TCPDBench/execs/python/venv/requirements.txt
RUN /bin/bash -c "source /TCPDBench/execs/python/venv/bin/activate && \
    pip install --upgrade pip && pip install -r /TCPDBench/execs/python/venv/requirements.txt"

# Copy PyTorch venv from Stage 1
COPY --from=pytorch-stage /venv_pytorch /TCPDBench/execs/python/venv_pytorch

# Install any system-wide Python packages if needed
COPY ${PROJECT_FOLDER}/requirements.txt /TCPDBench/requirements.txt
RUN python3.9 -m pip install setuptools==75.4.0
RUN python3.9 -m pip install -r /TCPDBench/requirements.txt

# Copy project files
COPY ${PROJECT_FOLDER}/Makefile /TCPDBench/Makefile
COPY ${PROJECT_FOLDER}/utils.R /TCPDBench/execs/R/utils.R
COPY ${PROJECT_FOLDER}/*.py /TCPDBench/execs/python/
COPY ${PROJECT_FOLDER}/*.R /TCPDBench/execs/R/
COPY ${PROJECT_FOLDER}/analysis/*.py /TCPDBench/analysis/scripts/
COPY ${DATASETS_PATH} /TCPDBench/datasets
COPY ${ANNOTATIONS_PATH} /TCPDBench/analysis/annotations/annotations.json
COPY ${SIG_ATTIBUTES} /TCPDBench/analysis/annotations/signatures_attributes.json

# Finalize dataset setup
RUN chmod +x utils/setup_datasets.sh && ./utils/setup_datasets.sh


# docker build --no-cache --build-arg DATASETS_PATH=data/temp_data/sp3-tp6-datasets-annotated-aggregated-jsonfied-400-samples-new-prod/all_timeseries --build-arg ANNOTATIONS_PATH=data/temp_data/sp3-tp6-datasets-annotated-aggregated-jsonfied-400-samples-new-prod/annotations.json --build-arg SIG_ATTIBUTES=data_annotation_platform/app/static/resources/timeseries_specs.json -t selected_400 -f prediction_generation/Dockerfile .