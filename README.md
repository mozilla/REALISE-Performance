## Context

The performance of large systems is crucial for business efficiency, as unresponsive systems can harm user experience and software quality. Companies, such as Mozilla, invest in performance testing and monitoring. We publish this dataset for the scientific community for them to investigate it and perform studies on it such on performance regression root cause analysis.


## Artifact structure


The artifact is organized like this: 

```
mozilla-data/
├── data/
│   ├── alerts_data.csv
│   ├── bugs_data.csv
│   ├── README.md
│   └── timeseries_data/
│       ├── autoland1/
│       │   ├── 4768977_timeseries_data.csv
│       │   ├── 4768979_timeseries_data.csv
│       │   └── .........
│       ├── autoland2/
│       │   ├── 4405584_timeseries_data.csv
│       │   ├── 4405588_timeseries_data.csv
│       │   └── .........
│       ├── autoland3/
│       │   ├── 3780010_timeseries_data.csv
│       │   ├── 3780011_timeseries_data.csv
│       │   └── .........
│       ├── autoland4/
│       │   ├── 1468481_timeseries_data.csv
│       │   ├── 1468482_timeseries_data.csv
│       │   └── .........
│       ├── firefox-android/
│       │   ├── 4653372_timeseries_data.csv
│       │   ├── 4653590_timeseries_data.csv
│       │   └── .........
│       ├── mozilla-beta/
│       │   ├── 1484905_timeseries_data.csv
│       │   ├── 1484929_timeseries_data.csv
│       │   └── .........
│       ├── mozilla-central/
│       │   ├── 1484905_timeseries_data.csv
│       │   ├── 1484929_timeseries_data.csv
│       │   └── .........
│       └── mozilla-release/
│           └── 2780728_timeseries_data.csv
└── scripts/
    ├── extract_alerts.py
    ├── artifact_paper_analysis.ipynb
    └── ... (other Python files and notebooks)
```


## Scripts overview

The `scripts` folder contains scripts and notebooks respectively to extract performance-related data from [Treeherder API](https://treeherder.mozilla.org/docs/), transform them, and do preliminary analysis on them. The scripts can also be used to re-collect and update the dataset to include newer performance measurements and alerts from Mozilla systems.



## Data overview

Performance-related data are extracted from one year ago (from beginning of May 2023 to the beginning of May 2024). The `data` folder containing the performance time series data, alerts and alerts summaries, and bugs. Performance time series are further organized into their respective repositories, and we store a single CSV per performance time series. Alerts and bugs, on the other hand, are stored on one CSV file each.  