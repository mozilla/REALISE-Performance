FROM simoneismann/tcpdbench:latest
ENV PROJECT_FOLDER='prediction_generation'
ARG ANNOTATIONS_PATH='annotations.json'
ARG DATASETS_PATH='datasets'
ARG SIG_ATTIBUTES='signatures_attributes.json'
# The problem with the base image is that it does not persist R package installations across Docker builds, so I am using the one from the image shared from the previous project directly. The only problem is that it is super heavy
# it is advised that if you do not need R packages installed, you delete the first and the third lines among the following three
RUN mv /TCPDBench/execs/R/rlibs /rlibs
RUN rm -rf /TCPDBench
COPY prediction_generation /TCPDBench
COPY .git /TCPDBench/.git
RUN mv /rlibs /TCPDBench/execs/R/rlibs
WORKDIR TCPDBench
RUN python3.9 -m venv /TCPDBench/execs/python/venv
RUN apt-get install nano python3.9-distutils python3.9-dev build-essential python3-distutils python3-setuptools -y
# Some methods that utilize Python instead of R (MongoDB and Prophet) need a virtual environment to be able to run
RUN /bin/bash -c "source /TCPDBench/execs/python/venv/bin/activate && pip install -r /TCPDBench/execs/python/venv/requirements.txt"
# Setuptools is installed separately because including it in the requirements.txt causes issues with rpy2 installation
RUN python3.9 -m pip install setuptools==75.4.0
RUN python3.9 -m pip install -r /TCPDBench/requirements.txt
RUN mkdir stagedir
COPY ${DATASETS_PATH} /TCPDBench/datasets
COPY ${ANNOTATIONS_PATH} /TCPDBench/analysis/annotations/annotations.json
COPY ${SIG_ATTIBUTES} /TCPDBench/analysis/annotations/signatures_attributes.json
RUN chmod +x utils/setup_datasets.sh && ./utils/setup_datasets.sh

# docker build --no-cache --build-arg DATASETS_PATH=data/temp_data/clean_data/sp3-tp6-datasets-annotated-aggregated-jsonfied-174-samples --build-arg ANNOTATIONS_PATH=data/temp_data/clean_data/annotations.json --build-arg SIG_ATTIBUTES=data_annotation_platform/app/static/resources/timeseries_specs.json -t mohamedbilelbesbes/selected_174_online_extension_dockerfile_refacotring:cliff -f prediction_generation/Dockerfile .