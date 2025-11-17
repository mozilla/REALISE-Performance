# Command to build: docker build --build-arg DATASETS_PATH=data/datasets-aggregated --build-arg ANNOTATIONS_PATH=data/annotations/sample_data/sp_is_fp/annotations.json -t avg-agg-original -f prediction_generation/Dockerfile .
FROM simoneismann/tcpdbench:latest
ENV PROJECT_FOLDER='prediction_generation'
ARG ANNOTATIONS_PATH='annotations.json'
ARG DATASETS_PATH='datasets'
ARG SIG_ATTIBUTES='signatures_attributes.json'
WORKDIR TCPDBench
RUN python3.9 -m venv /TCPDBench/execs/python/venv
COPY ${PROJECT_FOLDER}/requirements-venv.txt /TCPDBench/execs/python/venv/requirements.txt
RUN apt-get install nano python3.9-distutils python3.9-dev build-essential python3-distutils python3-setuptools -y
# Some methods that utilize Python instead of R (MongoDB and Prophet) need a virtual environment to be able to run
RUN /bin/bash -c "source /TCPDBench/execs/python/venv/bin/activate && pip install -r /TCPDBench/execs/python/venv/requirements.txt"
# Setuptools is installed separately because including it in the requirements.txt causes issues with rpy2 installation
RUN python3.9 -m pip install setuptools==75.4.0
COPY ${PROJECT_FOLDER}/requirements.txt /TCPDBench/requirements.txt
# Some methods that utilize Python instead of R (KCPA and zero) are utilizing the existing python3.9 installation.
RUN python3.9 -m pip install -r /TCPDBench/requirements.txt
COPY ${PROJECT_FOLDER}/make_table.py /TCPDBench/analysis/scripts/make_table.py
COPY ${PROJECT_FOLDER}/aggregate_table_wide.py /TCPDBench/analysis/scripts/aggregate_table_wide.py
COPY ${PROJECT_FOLDER}/cpdbench_utils.py /TCPDBench/execs/python/cpdbench_utils.py
COPY ${PROJECT_FOLDER}/summarize.py /TCPDBench/analysis/scripts/summarize.py
COPY ${PROJECT_FOLDER}/summarize_metrics.py /TCPDBench/analysis/scripts/summarize_metrics.py
COPY ${PROJECT_FOLDER}/utils.R /TCPDBench/execs/R/utils.R
COPY ${PROJECT_FOLDER}/cpdbench_wbs.R /TCPDBench/execs/R/cpdbench_wbs.R
COPY ${PROJECT_FOLDER}/cpdbench_prophet.py /TCPDBench/execs/python/cpdbench_prophet.py
COPY ${PROJECT_FOLDER}/cpdbench_mozilla_rep.py /TCPDBench/execs/python/cpdbench_mozilla_rep.py
COPY ${PROJECT_FOLDER}/cpdbench_mozilla_rep_cliff.py /TCPDBench/execs/python/cpdbench_mozilla_rep_cliff.py
COPY ${PROJECT_FOLDER}/cpdbench_page_hinkley.py /TCPDBench/execs/python/cpdbench_page_hinkley.py
COPY ${PROJECT_FOLDER}/cpdbench_chisquare.py /TCPDBench/execs/python/cpdbench_chisquare.py
COPY ${PROJECT_FOLDER}/cpdbench_page_hinkley_lookahead.py /TCPDBench/execs/python/cpdbench_page_hinkley_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_chisquare_lookahead.py /TCPDBench/execs/python/cpdbench_chisquare_lookahead.py
RUN mkdir stagedir
COPY ${PROJECT_FOLDER}/Makefile /TCPDBench/Makefile
COPY ${PROJECT_FOLDER}/cpdbench_ecp.R /TCPDBench/execs/R/cpdbench_ecp.R
COPY ${PROJECT_FOLDER}/cpdbench_kcpa.py /TCPDBench/execs/python/cpdbench_kcpa.py
COPY ${PROJECT_FOLDER}/cpdbench_adwin.py /TCPDBench/execs/python/cpdbench_adwin.py
COPY ${PROJECT_FOLDER}/cpdbench_ewma.py /TCPDBench/execs/python/cpdbench_ewma.py
COPY ${PROJECT_FOLDER}/cpdbench_kswin.py /TCPDBench/execs/python/cpdbench_kswin.py
COPY ${PROJECT_FOLDER}/cpdbench_cusum.py /TCPDBench/execs/python/cpdbench_cusum.py
COPY ${PROJECT_FOLDER}/cpdbench_sprt.py /TCPDBench/execs/python/cpdbench_sprt.py
COPY ${PROJECT_FOLDER}/cpdbench_odummy.py /TCPDBench/execs/python/cpdbench_odummy.py
COPY ${PROJECT_FOLDER}/cpdbench_shewhart.py /TCPDBench/execs/python/cpdbench_shewhart.py
COPY ${PROJECT_FOLDER}/cpdbench_mosum.py /TCPDBench/execs/python/cpdbench_mosum.py
COPY ${PROJECT_FOLDER}/cpdbench_cvm.py /TCPDBench/execs/python/cpdbench_cvm.py
COPY ${PROJECT_FOLDER}/cpdbench_adwin_lookahead.py /TCPDBench/execs/python/cpdbench_adwin_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_ewma_lookahead.py /TCPDBench/execs/python/cpdbench_ewma_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_kswin_lookahead.py /TCPDBench/execs/python/cpdbench_kswin_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_cusum_lookahead.py /TCPDBench/execs/python/cpdbench_cusum_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_sprt_lookahead.py /TCPDBench/execs/python/cpdbench_sprt_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_odummy_lookahead.py /TCPDBench/execs/python/cpdbench_odummy_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_shewhart_lookahead.py /TCPDBench/execs/python/cpdbench_shewhart_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_mosum_lookahead.py /TCPDBench/execs/python/cpdbench_mosum_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_cvm_lookahead.py /TCPDBench/execs/python/cpdbench_cvm_lookahead.py
COPY ${PROJECT_FOLDER}/cpdbench_bocpd_lookahead.R /TCPDBench/execs/R/cpdbench_bocpd_lookahead.R
COPY ${PROJECT_FOLDER}/cpdbench_methods.py /TCPDBench/execs/python/cpdbench_methods.py
COPY ${PROJECT_FOLDER}/cpdbench_methods_cliff.py /TCPDBench/execs/python/cpdbench_methods_cliff.py
COPY ${PROJECT_FOLDER}/abed_conf.py /TCPDBench/abed_conf.py
COPY ${DATASETS_PATH} /TCPDBench/datasets
COPY ${ANNOTATIONS_PATH} /TCPDBench/analysis/annotations/annotations.json
COPY ${SIG_ATTIBUTES} /TCPDBench/analysis/annotations/signatures_attributes.json
RUN chmod +x utils/setup_datasets.sh && ./utils/setup_datasets.sh

# docker build --no-cache --build-arg DATASETS_PATH=data/temp_data/clean_data/sp3-tp6-datasets-annotated-aggregated-jsonfied-174-samples --build-arg ANNOTATIONS_PATH=data/temp_data/clean_data/annotations.json --build-arg SIG_ATTIBUTES=data_annotation_platform/app/static/resources/timeseries_specs.json -t mohamedbilelbesbes/selected_174_online_extension:cliff -f prediction_generation/Dockerfile .