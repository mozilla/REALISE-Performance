## Overview
The following part presents the data existing in the replication package\cite{replicationpackage}, which contains the code for extracting the data from the Mozilla systems and the data itself.

`curated_alerts_data.csv` file: It contains the alerts curated and filtered after the refresh of the 'Still Processing' alert summaries.

`all-datasets` folder: It contains the time series data of the signatures related to the alerts described in the curated alerts CSV file. This is the raw data extracted in May 2024. The transformed and processed version of this data exists in `all-datasets-annotated` folder.

`all-datasets-annotated` folder: It contains the time series data of the signatures related to the alerts described in the curated alerts CSV file. It is cleaned, updated, and cross-referenced with the curated alerts CSV file.

`all-datasets-annotated-aggregated` folder: As for a specific time series, one revision usually corresponds to multiple measurements, we aggregated the measurements by revision. We apply this transformation on all the CSV files of all-datasets-annotated folder to obtain all-datasets-annotated-aggregated.

`bugs_data_from_api.csv` file: It contains the bugs data extracted from Mozilla API based on the bugs mentioned in the curated alerts CSV file.

`data_extraction_transformation` folder: It contains the necessary code for extracting the data (not the exact same data as the content will include the data from the last year, for example if the data extraction is being done in March 2025, the data to be obtained is the related to March 2024 up until March 2025). It also contains the analysis notebooks to conduct the analysis (including the code generating some of the graphs in this paper).


TODO: complete the description of the other files/folders (they are not needed for the artifacts challenge submission).

## Alerts/Alert summaries data:


The following definitions describe the attributes in the alerts CSV file. It is worth noting that the columns prefixed with `alert_summary_` as well as columns `push_timestamp` and `signature_id` represent attributes related to the alert summary associated with the gven alert, wherea columns prefixed with `single_alert_` are alert-specific:


- `push_timestamp`: The time in which the revision assocated with the given alert was pushed.
- `signature_id`: The signature from which the alert wa detected. A signature is a timeseries of performance measurements across subsequent revisions that is specific to one test running in one framework of mozilla's testing frameworks running on one project of Mozilla's projects running on one platform. This timeseries consists of many measurement points. Mozilla's Perfherder system enables performance sheriffs to visualize a given timeseries.
- `alert_summary_assignee_email`: The email address of the performance sheriff that the alert summary was assigne to.
- `alert_summary_assignee_username`: very similar to alert_summary_assignee_email, but for username instead of email address.
- `alert_summary_bug_due_date`: The deadline to resolve the bug associated with the alert summary.
- `alert_summary_bug_number`: The ID of the bug associated with the alert summary. If there is no bug associated yet, the value will be `NaN`.
- `alert_summary_bug_updated`: _It is a timestamp that seems to be the time when the bug associated with the alert summary was updated_.
- `alert_summary_creation_timestamp`: The timestamp of the alert summary creation.
- `alert_summary_first_triaged`: The timestamp of the first time the alert summary was triaged by a performance engineer. Untriaged alerts have `NaT` as a value of this attribute.
- `alert_summary_framework`:  The framework on which the testing ran for the alerts of the given alert summary.
- `alert_summary_id`: The ID of the alert summary.
- `alert_summary_issue_tracker`: _  NaN _.
- `alert_summary_notes`: Natural text notes written by performance engineers concerning the given alert summary
- `alert_summary_performance_tags`: _ NaN _.
- `alert_summary_prev_push_id`: _ NaN _.
- `alert_summary_prev_push_revision`: _ NaN _.
- `alert_summary_push_id`: _ NaN _.
- `alert_summary_related_alerts`: _ NaN _.
- `alert_summary_repository`: The repository in which the revision associated with the alert summary exists.
- `alert_summary_revision`: The revision associated with the alert summary.
- `alert_summary_triage_due_date`: The due date of triaging the given alert summary. It is generally between 2 and 4 days as it accounts for the weekend (detail stated [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perf/utils.py#L8)).
- `alert_summary_push_id`: _ NaN _.
- `alert_summary_status` and `single_alert_status` : Mozilla's performance team works to detect regressions and report them for mitigation. Each alert or alert summary has an assigned status. Below are the possible statuses:

  - **Untriaged**: These are alert summaries that have not yet been reviewed by the performance team. As such, they are not classified, making it difficult to determine if they are false positives or not.
  - **Downstream**: These alert summaries are triggered as a result of or are related to an original alert summary. They reflect additional issues or consequences stemming from the same root cause, providing a more comprehensive view of the problem.
  - **Reassigned**: These alert summaries have been reviewed, a verdict has been made, but they are reassigned for further review due to various reasons related to the performance engineering workflow.
  - **Invalid**: These alert summaries are typically due to noise and are considered false positives.
  - **Improvement**: These are alert summaries that indicate performance improvements detected by the system, in addition to potential regressions.
  - **Investigating**: These are alert summaries still under investigation.
  - **Wontfix**: These represent actual anomalies, but no action will be taken directly on them. Instead, actions will be taken on related alert summaries.
  - **Fixed**: This status indicates that the issue triggered by the alert summary has been resolved.
  - **Backedout**: This status means the changes that triggered the alert summary have been rolled back, usually because the changes caused a regression.
  - **Acknowledged**: This status indicates that a Performance Sheriff has reviewed the alert summary, so another Sheriff doesn't need to review it again.

  The Possible alert summary statuses are:
  - Untriaged
  - Downstream
  - Reassigned
  - Invalid
  - Improvement
  - Investigating
  - Wontfix
  - Fixed
  - Backedout

  The Possible alert statuses are:
  - Untriaged
  - Downstream
  - Reassigned
  - Invalid
  - Acknowledged

- `single_alert_amount_abs`: The ABS value associated with the alert. It is defined through code [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perf/alerts.py#L38).
- `single_alert_amount_pct`: The confidence probability associated with the alert. It is defined through code [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perf/alerts.py#L34).
- `single_alert_backfill_record_context`: _ NaN _.
- `single_alert_backfill_record_status`: _ NaN _.
- `single_alert_backfill_record_total_actions_triggered`: _ NaN _.
- `single_alert_backfill_record_total_backfills_failed`: _ NaN _.
- `single_alert_backfill_record_total_backfills_in_progress`: _ NaN _.
- `single_alert_backfill_record_total_backfills_successful`: _ NaN _.
- `single_alert_classifier`: _ The name of the perofrmance engineer classifying the alert  _.
- `single_alert_classifier_email`: : _ The email of the perofrmance engineer classifying the alert _.
- `single_alert_id`: The ID of the given alert.
- `single_alert_is_regression`: This attribute is `True` if Mozilla's performance anomaly detection system considers the alert presenting a regression and is `False` if it considers the alert as an improvement.
- `single_alert_manually_created`: is `True` if the alert was manually created by a Performance engineer and `False` if created by Mozilla's performance anomaly detection system.
- `single_alert_noise_profile`: _ NaN _.
- `single_alert_prev_profile_url`: _ NaN _.
- `single_alert_prev_taskcluster_metadata_retry_id`: _ NaN _.
- `single_alert_prev_taskcluster_metadata_task_id`: _ NaN _.
- `single_alert_prev_value`: It is an aggregated value of the performance measurements associated with a specific number of revisions preceding the revision under test. It is defined in code [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perf/alerts.py#L94). 
- `single_alert_new_value`: It is an aggregated value of the performance measurements of the revision under investigating and a handful of the measurements following it. It is defined in code [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perf/alerts.py#L94).
- `single_alert_profile_url`: _ NaN _.
- `single_alert_related_summary_id`
- `single_alert_series_signature_extra_options`
- `single_alert_series_signature_framework_id`: The framework ID associated with the signature from which the alert got triggered.
- `single_alert_series_signature_has_subtests`: _ NaN _.
- `single_alert_series_signature_lower_is_better`: It is `True` if the measurement is considered good if it goes down from revision to another and it is `False` otherwise.
- `single_alert_series_signature_machine_platform`: It is the platform aasociated with the signature of the given alert.
- `single_alert_series_signature_measurement_unit`: The measurement unit associated with the signature of the alert.
- `single_alert_series_signature_option_collection_hash`
- `single_alert_series_signature_signature_hash`: It is the hash of the signature of the given alert.
- `single_alert_series_signature_suite`: It is the test suite aasociated with the signature of the given alert.
- `single_alert_series_signature_suite_public_name`: _ It is supposed to present the full name of the test suite aasociated with the signature of the given alert. All its values are NaN _.
- `single_alert_series_signature_tags`: 
- `single_alert_series_signature_test_public_name`: _ It is supposed to present the full name of the test aasociated with the signature of the given alert. All its values are NaN _.
- `single_alert_starred`: It is set to `True` if the alert is starred (there is a clickable star icon on every alert) by a performance engineer and it is set to `False` it not.
- `single_alert_summary_id`: It is the same as `alert_summary_id` column.
- `single_alert_taskcluster_metadata_retry_id`: _ NaN _.
- `single_alert_taskcluster_metadata_task_id`: _ NaN _.
- `single_alert_t_value`: The value of magnitude of change associated with the alert. It is defined through code [here](https://github.com/mozilla/treeherder/blob/master/treeherder/perfalert/perfalert/__init__.py#L157).
- `single_alert_series_signature_test`: It is the test aasociated with the signature of the given alert.

## Timeseries data

The timeseries data, also said a signature data, contains the alerts data in the folders that were a result of cross-referencing the alerts data and the raw timeseries data. The columns are those of alerts are identical to the ones in the alerts/alert summaries CSV and the remaining columns are as follows:



- `repository_name`: The name of the repository associated with the signature.
- `signature_id`: The signature from which the alert wa detected. A signature is a timeseries of performance measurements across subsequent revisions that is specific to one test running in one framework of mozilla's testing frameworks running on one project of Mozilla's projects running on one platform. This timeseries consists of many measurement points. Mozilla's Perfherder system enables performance sheriffs to visualize a given timeseries.
- `framework_id`: The ID of the framework associated with the signature. An example of a framework is [Talos](https://firefox-source-docs.mozilla.org/testing/perfdocs/talos.html).
- `signature_hash`: It is the hash of the signature.
- `machine_platform`: It is the platform aasociated with the signature. A platform is a combination of software and hardware configuration on which performance tests can run.
- `should_alert`: _ NaN _.
- `has_subtests`: _ NaN _.
- `extra_options`: _ NaN _.
- `tags`: _ NaN _.
- `option_collection_hash`: _ NaN _.
- `test`: The name of the test associated with the signature.
- `suite`: The name of the test suite associated with the signature.
- `lower_is_better`: It is `True` if the measurement is considered good if it goes down from revision to another and it is `False` otherwise.
- `name`: _ NaN _.
- `parent_signature`: _ NaN _.
- `repository_id`: The ID of the repository associated with the signature.
- `measurement_unit`: The measurement unit associated with the signature. It could be something such as milliseconds or byte for example.
- `application`: It represents the application or product associated with the signature. For example, Firfox cold be considered a product.
- `job_id`: _ NaN _.
- `entry_id`: _ NaN _.
- `value`: It represents the given perofrmance measurement. One revision in one signature could have multiple measurements.
- `revision`: The revision associated with the given measurement.
- `push_id`: _ NaN _.

## Bugs data

- `id`: A unique identifier for the bug report.
- `type`: The type or category of the bug (e.g., defect, enhancement).
- `summary`: A brief description of the bug or issue.
- `status`: The current state of the bug (e.g., new, in-progress, resolved, closed).
- `priority`: The urgency or importance level assigned to the bug.
- `severity`: The impact level of the bug on the system or user experience.
- `creator`: The performance engineer who created or reported the bug.
- `assigned_to`: The performance engineer currently responsible for addressing the bug.
- `creation_time`: The timestamp when the bug report was created.
- `last_change_time`: The timestamp of the most recent update to the bug report.
- `component`: The specific module or feature affected by the bug.
- `product`: The product or project associated with the bug.
- `resolution`: The outcome or solution applied to the bug (e.g., fixed, won't fix, duplicate).
- `is_confirmed`: A boolean indicating whether the bug has been verified or confirmed.
- `platform`: The hardware or software platform where the bug was observed.
- `op_sys`: The operating system where the bug occurs.
- `assigned_to_name`: The name of the performance engineer assigned to the bug.
- `assigned_to_email`: The email address of the performance engineer assigned to the bug.
- `cc`: A list of performance engineers or email addresses copied on updates to the bug.
- `cc_detail`: Detailed information about the performance engineers or email addresses in the CC list.
- `flags`: Additional flags or metadata associated with the bug report.
- `classification`: The broader classification or category for the bug (e.g., security, usability).
- `triage_owner`: The performance engineer responsible for triaging or managing the bug report.
- `comment_count`: The total number of comments on the bug report.
- `keywords`: Keywords or tags associated with the bug report.
- `depends_on`: A list of bug IDs that this bug depends on.
- `blocks`: A list of bug IDs that this bug blocks.
- `duplicates`: A list of bug IDs that are duplicates of this bug.
- `creator_name`: The name of the performance engineer who reported the bug.
- `creator_email`: The email address of the performance engineer who reported the bug.
