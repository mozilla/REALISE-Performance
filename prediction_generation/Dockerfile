# Command to build: docker build --build-arg DATASETS_PATH=data/datasets-aggregated --build-arg ANNOTATIONS_PATH=data/annotations/sample_data/sp_is_fp/annotations.json -t avg-agg-original -f prediction_generation/Dockerfile .
FROM simoneismann/tcpdbench:latest
ENV PROJECT_FOLDER='prediction_generation'
ARG ANNOTATIONS_PATH='annotations.json'
ARG DATASETS_PATH='datasets'
ARG SIG_ATTIBUTES='signatures_attributes.json'
WORKDIR TCPDBench
COPY ${PROJECT_FOLDER}/make_table.py /TCPDBench/analysis/scripts/make_table.py
COPY ${PROJECT_FOLDER}/aggregate_table_wide.py /TCPDBench/analysis/scripts/aggregate_table_wide.py
COPY ${PROJECT_FOLDER}/cpdbench_utils.py /TCPDBench/execs/python/cpdbench_utils.py
COPY ${PROJECT_FOLDER}/summarize.py /TCPDBench/analysis/scripts/summarize.py
COPY ${PROJECT_FOLDER}/summarize_metrics.py /TCPDBench/analysis/scripts/summarize_metrics.py
COPY ${PROJECT_FOLDER}/utils.R /TCPDBench/execs/R/utils.R
COPY ${PROJECT_FOLDER}/cpdbench_wbs.R /TCPDBench/execs/R/cpdbench_wbs.R
COPY ${PROJECT_FOLDER}/cpdbench_prophet.py /TCPDBench/execs/python/cpdbench_prophet.py
COPY ${PROJECT_FOLDER}/cpdbench_mozilla_rep.py /TCPDBench/execs/python/cpdbench_mozilla_rep.py
RUN python3.9 -m venv /TCPDBench/execs/python/venv
COPY ${PROJECT_FOLDER}/requirements-venv.txt /TCPDBench/execs/python/venv/requirements.txt
RUN apt-get install nano
# Some methods that utilize Python instead of R (MongoDB and Prophet) need a virtual environment to be able to run
RUN /bin/bash -c "source /TCPDBench/execs/python/venv/bin/activate && pip install -r /TCPDBench/execs/python/venv/requirements.txt"
# Some methods that utilize Python instead of R (KCPA and zero) are utilizing the existing python3.9 installation.
# Setuptools is installed separately because including it in the requirements.txt causes issues with rpy2 installation
RUN python3.9 -m pip install setuptools==75.4.0
COPY ${PROJECT_FOLDER}/requirements.txt /TCPDBench/requirements.txt
RUN python3.9 -m pip install -r /TCPDBench/requirements.txt
RUN mkdir stagedir
COPY ${PROJECT_FOLDER}/Makefile /TCPDBench/Makefile
COPY ${PROJECT_FOLDER}/cpdbench_ecp.R /TCPDBench/execs/R/cpdbench_ecp.R
COPY ${PROJECT_FOLDER}/cpdbench_kcpa.py /TCPDBench/execs/python/cpdbench_kcpa.py
COPY ${PROJECT_FOLDER}/abed_conf.py /TCPDBench/abed_conf.py
ADD ${DATASETS_PATH} /TCPDBench/datasets
COPY ${ANNOTATIONS_PATH} /TCPDBench/analysis/annotations/
COPY ${SIG_ATTIBUTES} /TCPDBench/analysis/annotations/
RUN chmod +x utils/setup_datasets.sh && ./utils/setup_datasets.sh

# docker build --build-arg DATASETS_PATH=data/195_non_sp_at_least_one_fp_fn_samples_json_aggregated --build-arg ANNOTATIONS_PATH=data/195_non_sp_at_least_one_fp_fn_samples_json_aggregated/annotations.json --build-arg SIG_ATTIBUTES=data/temp_data/195_non_sp_at_least_one_fp_fn_samples_attribute.json -t non_sp_at_least_one_fn_fp -f prediction_generation/Dockerfile .