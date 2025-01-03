***Files definitions***

This folder contains the code to extract and transform performance-related data under `scripts`. The transformations are statistical tranformations such as minmax scaling and transformations to fit the data into a system called [`TCPDBench`](../prediction_generation/original-project) The generated data resides in the `datasets` folder. It also contains notebooks for the data analysis under `notebooks` to durther understand the problematic. The notebooks are self-explanatory.
The code files directly under `scripts` folder have definitions that is obtained by running `python <python_file_path> --help`

***Running scripts***

0. In order to run the scripts, make sure to have Python 3.12 or above as well as pip in the running environment (Python 3.12.2 was used during scripts development). Afterwards, make sure to run : 
```
pip install -r requirements.txt
```
Also, you need to access the `scripts` folder under this folder : 
```
cd scripts
```

1. In order to run the script to extract the alerts, run `extract-alerts.py`
It will generate the aelrt data CSV (for example `alerts_data.csv`) which will have the performance alerts data from the time of running the script all the waty back to one year before that.

2. Once you have the alerts CSv, you can extract their associated bugs. In order to run the script to extract the bugs, run either `extract-bugs-bugbug.py` or `extract-bugs-api.py`
It will generate the bugs CSV (for example `bugs_data.csv`) which will have all the bugs associated with the alerts extracted inthe earlier alerts CSV.

3. In order to run the script to extract the timeseries data, make sure to run `extract-timseries.py`
Note that for the case of autoland, timeseries files were divided across multiple folders because github does not support pushing a folder with more than 1000 files in them. The splitting process took place manually.

> **Note**
> In case the alerts CSV and the timeseries data ectraction are not done back-to-back, there might be situation where some of the oldest alerts will not cross-reference with any of the timeseries. There could be also a situation where new alerts got triggered that would cross-rzference with a specific timeseries but the problem is that the new alerts doesn't exist in the alerts CSV (given that they were extracted earlier than the alert creation). SO, for data consistency purposes, please extract the alerts CSV and the timeseries data back-to-back.

4. Proceed with cross-referencing the timeseries CSVs with the alerts CSV.n order to run the script to extract the alerts, run `transform-data.py`. Note that the scripts contains the folders mapping to projects because autoland has 4 associated folders as mentionned earlier.

5. Optional: you can run data transformations on the timeseries (smoothing using `smoothe.py`, minmax scaling using `minmaxscale.py`, aggregation using `aggregate.py`, or a combination of some of them). This will output CSV files same as the previously extracted timeseries ones, with a change only occurring in the measurements

6. Convert the CSV data to JSON format in a way that could be ingested by TCPDBench. You can transform your data using `jsonfy-timeseries.py`.

7. The timeseries data could be extensive and only a subset of it is needed to run it in TCPDBench. So, using `handpick_specific_files.py`, you could isolate only specific timeseries (the script handles isolating their annotations file too).