***Folder Overview***

This folder contains the code to extract and transform performance-related data. The transformations are statistical tranformations such as minmax scaling and transformations to fit the data into a system called `TCPDBench`.
The code files have definitions that are obtained by running `python <python_file_path> --help`.

In order to run the scripts, make sure to have Python 3.12 or above as well as pip in the running environment (Python 3.12.2 was used during scripts development). Afterwards, make sure to run : 
```
pip install -r requirements.txt
```

***Scripts for extracting data***

- In order to run the script to extract the alerts, run `extract_alerts.py`
It will generate the alert data CSV (for example `alerts_data.csv`) which will have the performance alerts data from the time of running the script all the waty back to one year before that.

- Once you have the alerts CSV, you can extract their associated bugs. In order to run the script to extract the bugs, run `extract_bugs.py`
It will generate the bugs CSV (for example `bugs_data.csv`) which will have all the bugs associated with the alerts extracted inthe earlier alerts CSV.

- In order to run the script to extract the timeseries data, make sure to run `extract_timseries.py`.

- In order to extract the jobs data associated with the collected performance measurements, run `extract_jobs.py`.

- Some extracted alerts are in untriaged or investigating status at the time of extracting the alerts extraction. These alerts could be updated by running the `update_still_processing_alerts.py` file.

***Transforming data***

- In order to cross-reference the timeseries CSVs with the alerts CSV, run `transform_data.py`.

- You can run data transformations on the timeseries (smoothing using `smoothe.py`, minmax scaling using `minmaxscale.py`, aggregation using `aggregate.py`, or a combination of some of them). This will output CSV files same as the previously extracted timeseries ones, with a change only occurring in the measurements.

- Convert the CSV data to JSON format in a way that could be ingested by TCPDBench. You can transform data using `jsonfy_timeseries.py`.

- The timeseries data could be extensive and only a subset of it is needed to run it in TCPDBench. So, using `handpick_specific_csv_files.py` or `handpick_specific_json_files.py`, you could isolate only specific timeseries (the script handles isolating their annotations file too).

- `extract_signatures_properties.py` extracts the properties of the timeseries into a JSON.

- `CSVfy_JSONs.py` file: It transforms the timeseries CSV files containing performance measurements into JSON files ready to be used by `TCPDBench`.