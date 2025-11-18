# Turing Change Point Detection Benchmark
This is a fork of the [TCPDBench](https://github.com/SimonEismann/TCPDBench) with the goal to make it easier to configure and deploy. This fork only supports one-dimensional datasets!

## Running the experiments with Docker

1. Make sure to have a Docker host setup as a prerequisite.

2. Maake sure that you have a folder of your data JSONfied using [this](../data_extraction_transformation/scripts/jsonfy-timeseries.py) script. Make sure to have the ```annotations.json``` file in a separate folder than the one having the timeseries data JSONfied. Make sure to have the timeseries signatures proiperties extracted into a JSON file using [script](../scripts/one_time_use_scripts/extract_signatures_properties.py). Replace the paths of these artifacts in the command below.
3. Run the commands below in the Dockerfile directory to execute the experiments:

```shell
cd REALISE-Performance
# build a container from your created Dockerfile
docker build --no-cache --build-arg DATASETS_PATH=<REPLACE_VALUE> --build-arg ANNOTATIONS_PATH=<REPLACE_VALUE> --build-arg SIG_ATTIBUTES=<REPLACE_VALUE> -t tcpdexperiment -f prediction_generation/Dockerfile .
# make results persist to host
docker volume create tcpdbench_vol
# reproduce all experiments (-np sets number of threads)
docker run -i -t -v tcpdbench_vol:/TCPDBench/docker_results tcpdexperiment /bin/bash -c "abed reload_tasks && abed status && mpiexec --allow-run-as-root -np 4 abed local && make mozillasummary && cp -r /TCPDBench/abed_results /TCPDBench/docker_results && cp -r /TCPDBench/analysis/output /TCPDBench/docker_results"
# lookup the mountpoint of the volume --> there the results are stored
docker volume inspect tcpdbench_vol
```
You will find the needed LaTeX talbe under ```analysis/output/tables/latex_summary.tex```.