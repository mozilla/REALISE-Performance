## Context

The performance of large systems is crucial for business efficiency, as unresponsive systems can harm user experience and software quality. Companies, such as Mozilla, invest in performance testing and monitoring. We publish this dataset for the scientific community for them to investigate it and perform studies on it such on performance regression root cause analysis.

## Work done

Currently, the work done has revolved around extracting data from Mozilla system and try different change point detection techniques to detect anomalies in Mozilla data. The work that has been done exists in the folders `data` and `scripts`. Both of them have explanatory README files. Check them out for more details.
## scripts & notebooks overview

The `scripts` folder contains scripts and notebooks respectively to extract performance-related data from [Treeherder API](https://treeherder.mozilla.org/docs/), tranform them, and do preliminary analysis on them. Performance-related alerts are extracted from one year ago (from beginning of May 2023 to the beginning of May 2024).

The artifact is organized like this: 

```
repository/
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

## data overview

The `data` folder contains the data extracted and curated through the scripts in `scripts`. Please refer to the REAME inside the `data` folder.