#!/bin/bash

# create a python array with the dataset names and replace DATASETPLACEHOLDER

DATASET_LIST=(`ls /TCPDBench/datasets | grep -Po '.+(?=\.json)'`)
STR='['

for dataset in "${DATASET_LIST[@]}"; do
  STR="${STR}\"${dataset}\", "
done

STR="${STR::-2}]"

sed -i "s/DATASETPLACEHOLDER/${STR}/g" /TCPDBench/abed_conf.py
sed -i "s/DATASETPLACEHOLDER/${STR}/g" /TCPDBench/analysis/scripts/make_table.py
