## Context

The performance of large systems is crucial for business efficiency, as unresponsive systems can harm user experience and software quality. Companies, such as Mozilla, invest in performance testing and monitoring, but these are typically conducted outside the development context, often during pre-release QA which causes inefficiencies leading to resources/time loss.

## Vision

We want to **incorporate performance assessment during the code review process**. Upon submitting a patch for review, the solution should :
- Identify performance tests covering code changes & run them for comparison with historical data.
- Analyze the differences in the performance across the relevant performance metrics & include an actionable report in the code review.
- Optionally allow requesting further details on code change impact performance-wise

## Challenges

In order to make the vision concrete, the project is divided to multiple challeneges
- Challenge 0: **Exploring the performance test suite of Mozilla projects**
During this step, we analyze Mozilla's current performance testing and analysis practices to determine how the performance tests can be used within the code review workflow. 
- Challenge 1: **Mitigating the noise in the performance measurement data**

Multiple factors can influence performance measurements (e.g., hardware, other software systems competing for resources, different testing workloads, compiler optimizations, etc.), causing a lot of noise in the measurements. This noise in the data may trigger false performance alerts, wasting the time and resources of the development and operations team. The gist of this step is **to reduce noise in the generated data or to better identify it from the existing data with the aim of reducing false positive performance-related alerts.**

- Challenge 2: **Selecting relevant performance tests for fast performance assessment**

Mozilla’s performance testing suite is comprehensive and time-consuming to run at a patch level. The full performance test suite takes 138 CPU hours to run. We need to find ways to reduce the time it takes to run performance tests to give timely feedback during code review. Multiple strategies are put in place to tackle this problem :
  - Selecting a small set of the most relevant performance tests
  - Prioritizing running performance tests on “performance-sensitive code changes.”
  - Generating small performance tests (e.g., microbenchmarks) in the system critical path
- Challenge 3: **Handling gradual performance change**
Gradual changes that bypass change point detection methods may cause hard-to-fix performance regressions in the long term. The strategy we're aiming to apply to mitigate this challenge is to include long-term data analysis (e.g., trends,  autoregression) as part of the alert triggering mechanism by applying trend detection methods such as **change point detection**.
- Challenge 4: **Integrating performance metrics in the code review workflow**
Based on experience, performance tests can generate a lot of data that can overwhelm developers during code review. We need to plan how to communicate performance test results to developers in a way that is **1. actionable** and **2. informative**. The strategy to applied to overcome the challenge is to Incorporate the performance testing results as a bot solution in code review where developers can interact with the bot to request more tests to confirm the shown results as well as performance timeseries plots.

## project1 overview

The `project1` folder contains scripts (under `project1/scripts`) to extract performance-related data from [Treeherder API](https://treeherder.mozilla.org/docs/) and [bugbug](https://github.com/mozilla/bugbug). Performance-related alerts are extracted from one year ago (from beginning of May 2023 to the beginning of May 2024). Data associated with bugs and signatures from these alerts is extracted respectively (and saved under `project1/datasets`) and the data is utilized for analysis through Python notebooks (under `project1/notebooks`). For detailed information, refer to the [README.md](project1/README.md) file of the project.

## Contact information

This work is a collaboration between Mozilla and REALISE Lab in Concordia University. Lab members participating in the project are : 
- Prof. Diego Elias Costa (Supervising Professor)
- Mohamed Bilel Besbes (Research assistant)

![Concordia logo](assets/concordia-logo.png)
