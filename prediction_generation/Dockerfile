FROM simoneismann/tcpdbench:latest
WORKDIR TCPDBench
COPY annotations.json /TCPDBench/analysis/annotations/
#RUN rm /TCPDBench/analysis/scripts/make_table.py
COPY make_table.py /TCPDBench/analysis/scripts/make_table.py
#COPY simulation/analysis/scripts/summarize_metrics.py /TCPDBench/analysis/scripts/summarize_metrics.py
#RUN rm /TCPDBench/analysis/scripts/aggregate_table_wide.py
COPY aggregate_table_wide.py /TCPDBench/analysis/scripts/aggregate_table_wide.py
#RUN rm /TCPDBench/Makefile
#RUN rm /TCPDBench/execs/R/utils.R
#RUN rm /TCPDBench/execs/R/cpdbench_wbs.R
#RUN rm /TCPDBench/execs/R/cpdbench_prophet.R
#RUN rm /TCPDBench/execs/python/cpdbench_utils.py
#RUN rm /TCPDBench/analysis/scripts/summarize.py
COPY cpdbench_utils.py /TCPDBench/execs/python/cpdbench_utils.py
COPY summarize.py /TCPDBench/analysis/scripts/summarize.py
COPY summarize_metrics.py /TCPDBench/analysis/scripts/summarize_metrics.py
COPY utils.R /TCPDBench/execs/R/utils.R
COPY cpdbench_wbs.R /TCPDBench/execs/R/cpdbench_wbs.R
COPY cpdbench_prophet.py /TCPDBench/execs/python/cpdbench_prophet.py
#RUN rm -rf /TCPDBench/execs/python/mongodb
#RUN mkdir p /TCPDBench/execs/python/prophet && chmod 755 /TCPDBench/execs/python/prophet
RUN python3.9 -m venv /TCPDBench/execs/python/venv
COPY requirements.txt /TCPDBench/execs/python/venv/requirements.txt
RUN apt-get install nano
RUN /bin/bash -c "source /TCPDBench/execs/python/venv/bin/activate && pip install -r /TCPDBench/execs/python/venv/requirements.txt"
RUN python3.9 -m pip install signal-processing-algorithms==2.0.0 ruptures==1.1.9 numpy==1.21.5
RUN python3.9 -m pip install --upgrade setuptools
RUN python3.9 -m pip install rpy2
RUN mkdir stagedir
COPY Makefile /TCPDBench/Makefile
#COPY cpdbench_ecp.py /TCPDBench/execs/python/cpdbench_ecp.py
COPY cpdbench_ecp.R /TCPDBench/execs/R/cpdbench_ecp.R
COPY cpdbench_kcpa.py /TCPDBench/execs/python/cpdbench_kcpa.py
COPY abed_conf.py /TCPDBench/abed_conf.py
ADD datasets /TCPDBench/datasets
RUN chmod +x utils/setup_datasets.sh && ./utils/setup_datasets.sh