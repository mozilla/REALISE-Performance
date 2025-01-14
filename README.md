## Context

The performance of large systems is crucial for business efficiency, as unresponsive systems can harm user experience and software quality. Companies, such as Mozilla, invest in performance testing and monitoring. We publish this dataset for the scientific community for them to investigate it and perform studies on it such on performance regression root cause analysis.

## Work done

Currently, the work done has revolved around extracting data from Mozilla system and try different change point detection techniques to detect anomalies in Mozilla data. The work that has been done exists in the folders `data` and `data_extraction_transformation`. Both of them have explanatory REAME files. CHeck them out for more details.
## data_extraction_transformation overview

The `data_extraction_transformation` folder contains scripts and notebooks to extract performance-related data from [Treeherder API](https://treeherder.mozilla.org/docs/), tranform them, and do preliminary analysis on them. Performance-related alerts are extracted from one year ago (from beginning of May 2023 to the beginning of May 2024).

## Data artifacts challenge

The folders to consider for the artifacts challenge are `data` which contains the data and `data_extraction_transformation` which contains the necessary code used to extract the data.
