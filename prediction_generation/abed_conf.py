import copy

##############################################################################
#                                General Settings                            #
##############################################################################
PROJECT_NAME = "cpdbench"
TASK_FILE = "abed_tasks.txt"
AUTO_FILE = "abed_auto.txt"
RESULT_DIR = "./abed_results"
STAGE_DIR = "./stagedir"
PRUNE_DIR = "./pruned"
MAX_FILES = 1000
ZIP_DIR = "./zips"
LOG_DIR = "./logs"
OUTPUT_DIR = "./output"
AUTO_SLEEP = 120
HTML_PORT = 8000
COMPRESSION = "bzip2"
RESULT_EXTENSION = ".json"

##############################################################################
#                          Server parameters and settings                    #
##############################################################################
REMOTE_USER = "username"
REMOTE_HOST = "address.of.host"
REMOTE_DIR = "/home/%s/projects/%s" % (REMOTE_USER, PROJECT_NAME)
REMOTE_PORT = 22
REMOTE_SCRATCH = None
REMOTE_SCRATCH_ENV = "TMPDIR"

##############################################################################
#                      Settings for Master/Worker program                    #
##############################################################################
MW_SENDATONCE = 1  # number of tasks (hashes!) to send at once
MW_COPY_WORKER = False
MW_COPY_SLEEP = 120
MW_NUM_WORKERS = None

##############################################################################
#                               Experiment type                              #
##############################################################################
# Uncomment the desired type
# Model assessment #
TYPE = "ASSESS"

# Cross validation with train and test dataset #
# TYPE = 'CV_TT'
# CV_BASESEED = 123456
# YTRAIN_LABEL = 'y_train'

# Commands defined in a text file #
# TYPE = 'RAW'
# RAW_CMD_FILE = '/path/to/file.txt'

##############################################################################
#                                Build settings                              #
##############################################################################
NEEDS_BUILD = False  # If remote compilation is required
BUILD_DIR = "build"  # Relative directory where build takes place
BUILD_CMD = "make all"  # Build command

##############################################################################
#                      Experiment parameters and settings                    #
##############################################################################
DATADIR = "datasets"
EXECDIR = "execs"

DATASETS = DATASETPLACEHOLDER

DATASETS = ["3599323", "3776819"]

DATASET_NAMES = {k: k for k in DATASETS}

'''
METHODS = [
    "best_bocpd", # EN COURS (local macmini)
    "best_cpnp", # EN COURS (local macmini)
    "best_pelt", # EN COURS (local macmini)
    "best_amoc", # EN COURS (local macmini)
    "best_segneigh",
    "best_binseg", FINIS (remote macmini)
    "best_rfpop", # FINIS (remote macmini)
    "best_ecp", # EN COURS (local macmini)
    "best_kcpa", # FINIS (remote macmini)
    "best_wbs", # EN COURS (local macmini)
    "best_prophet",
    "best_zero", # EN COURS (local macmini)
    "best_mongodb", # FINIS (remote macmini)
    "default_bocpd", # EN COURS (local macmini)
    "default_cpnp", # EN COURS (local macmini)
    "default_pelt", # EN COURS (local macmini)
    "default_amoc", # EN COURS (local macmini)
    "default_segneigh",
    "default_binseg", FINIS (remote macmini)
    "default_rfpop", # FINIS (remote macmini)
    "default_ecp", # EN COURS (local macmini)
    "default_kcpa", # FINIS (remote macmini)
    "default_wbs", # EN COURS (local macmini)
    "default_prophet",
    "default_zero", # EN COURS (local macmini)
    "default_mongodb", # FINIS (remote macmini)
]

'''
METHODS = [
    "best_pelt",
    "default_pelt",
]


# many of these combinations will be invalid for the changepoint package, but
# it's easier to do it this way than to generate only the valid configurations.
R_changepoint_params = {
    "function": ["mean", "var", "meanvar"],
    "penalty": [
        "None",
        "SIC",
        "BIC",
        "MBIC",
        "AIC",
        "Hannan-Quinn",
        "Asymptotic",
    ],
    "statistic": ["Normal", "CUSUM", "CSS", "Gamma", "Exponential", "Poisson"],
}
R_changepoint_params_seg = copy.deepcopy(R_changepoint_params)
R_changepoint_params_seg["Q"] = ["max", "default"]

PARAMS = {
    "best_bocpd": {
        "intensity": [50, 100, 200],
        "prior_a": [0.01, 1.0, 100],
        "prior_b": [0.01, 1.0, 100],
        "prior_k": [0.01, 1.0, 100],
    },
    "best_cpnp": {
        "penalty": [
            "None",
            "SIC",
            "BIC",
            "MBIC",
            "AIC",
            "Hannan-Quinn",
            "Asymptotic",
        ],
        "quantiles": [10, 20, 30, 40],
    },
    "best_pelt": R_changepoint_params,
    "best_amoc": R_changepoint_params,
    "best_segneigh": R_changepoint_params_seg,
    "best_binseg": R_changepoint_params_seg,
    "best_rfpop": {"loss": ["L1", "L2", "Huber", "Outlier"]},
    "best_ecp": {
        "algorithm": ["e.agglo", "e.divisive"],
        "siglvl": [0.01, 0.05],
        "minsize": [2, 30],
        "alpha": [0.5, 1.0, 1.5],
        "runs": [100, 200, 500],
    },
    "best_kcpa": {
        "maxcp": [2, 5, 10],
        "minsize": [2, 3, 5],
        "kernel": ["linear", "rbf"]
    },
    "best_wbs": {
        "Kmax": ["max", "default"],
        "penalty": ["SSIC", "BIC", "MBIC"],
        "integrated": ["true", "false"],
    },
    "best_prophet": {"Nmax": ["max", "default"],
        "ChangepointRange": [0.6, 0.8, 0.95],
        "ChangepointPriorScale": [0.001, 0.1, 0.5],
        "IntervalWidth": [0.6, 0.8, 0.95],
        "growth": ['linear', 'logistic']
    },
    "best_zero": {"no_param": [0]},
    "best_mongodb": {
        "pvalue": [0.01, 0.05],
        "permutations": [10, 20, 50, 100, 150, 200],
    },
    "best_adwin": {
        "delta": [0.001, 0.002, 0.005, 0.01, 0.02]
    },
    "best_page_hinkley": {
        "min_instances": [10, 20, 30, 50],
        "delta": [0.001, 0.005, 0.01],
        "threshold": [10.0, 30.0, 50.0, 100.0],
        "alpha": [0.99, 0.999, 0.9999],
        "mode": ["up", "down", "both"]
    },
    "best_chisquare": {
        "window_size": [1.0, 2.5, 5.0, 7.5, 10.0], # Window size has to be between 1 and 10% as interpreted from here: https://centre-borelli.github.io/ruptures-docs/user-guide/detection/window/
        "num_bins": [5, 10, 20, 30], # Number of bins more than 5, around 30 as interpreted here: https://arxiv.org/html/2412.11158v1
        "p_threshold": [0.001, 0.005, 0.01, 0.02, 0.05], # p < 0.05 as a detection trigger as interpreted here: https://arxiv.org/html/2412.11158v1
        "min_distance": [10, 20, 30, 50, 100]
    },
    "best_kswin": {
        "alpha": [0.001, 0.005, 0.01, 0.02],
        "window_size": [100, 150, 199],
        "stat_size": [10, 20, 50]
    },
    "best_cusum": {
        "k": [1.0, 2.0, 3.0, 4.0, 5.0],
        "h": [30.0, 50.0, 75.0, 100.0, 150.0, 200.0], # h is recommended to be multiples of σ as interpreted here: https://arxiv.org/abs/2206.06777 . In this case, static values are used
        "init_size": [2.0, 5.0, 10.0, 15.0, 20.0], # Initial size proposed hyperparameter values are inspired from the following documentation: https://www.mathworks.com/help/signal/ref/cusum.html
        "min_distance": [50, 100, 150, 200, 300] # values reandomly selected
    },
    "best_ewma": {
        "alpha": [0.1, 0.2, 0.3], # nan aplha value of around 0.5 was used here in 11.1 : https://people.irisa.fr/Michele.Basseville/kniga/kniga.pdf
        "threshold": [2.5, 2.7, 3.0, 3.3], # threshold value is recommended to be multiples of σ as interpreted here: https://homepages.laas.fr/owe/METROSEC/DOC/Detection%20of%20intrusions%20in%20information%20systems%20by%20sequential%20change%20point%20methods.pdf. In this case, static values are used
        "init_size": [5.0, 10.0, 15.0],
        "min_distance": [20, 30, 50] # As per 9.3 and 10.2 from thids book: https://sadbhavnapublications.org/research-enrichment-material/2-Statistical-Books/Outlier-Analysis.pdf , the window value should be small enough
    },
    "best_shewhart": {
        "threshold": [2.5, 3.0, 3.5], # threshold value is recommended to be multiples of σ as interpreted here: https://homepages.laas.fr/owe/METROSEC/DOC/Detection%20of%20intrusions%20in%20information%20systems%20by%20sequential%20change%20point%20methods.pdf
        "init_size": [5.0, 10.0, 15.0], # values selected based on the following publication (III-A): https://arxiv.org/html/2408.06620
        "min_distance": [20, 30, 50] # size is interpreted from the following documentation: https://stackoverflow.com/questions/12709853/python-running-cumulative-sum-with-a-given-window
    },
    "best_odummy": {
        "trigger_method": ["fixed", "random"],
        "t_0": [100, 200, 300, 500],
        "w": [1, 50, 100],
        "init_size": [5.0, 10.0, 15.0],
        "min_distance": [20, 30, 50],
        "seed": [42]
    },
    "best_mosum": {
        "window_size": [10, 20, 30, 40, 50], # Window size has to be between 1 and 10% as interpreted from here: https://centre-borelli.github.io/ruptures-docs/user-guide/detection/window/
        "threshold": [1.0, 2.0, 3.0, 4.0, 5.0], # value are selected randomly
        "min_distance": [10, 20, 30, 40, 50], # size is interpreted from the following documentation: https://stackoverflow.com/questions/12709853/python-running-cumulative-sum-with-a-given-window
    },
    "best_sprt": {
        "mu0": [0.0], # values of m0, m1, and sigma inspired from this: https://mattlapa.com/sprt
        "mu1": [0.5, 1.0, 1.5], # values of m0, m1, and sigma inspired from this: https://mattlapa.com/sprt
        "sigma": [1.0], # values of m0, m1, and sigma inspired from this: https://mattlapa.com/sprt
        "threshold": [10.0, 15.0, 20.0],
        "min_distance": [10, 20, 30], # size is interpreted from the following documentation: https://stackoverflow.com/questions/12709853/python-running-cumulative-sum-with-a-given-window
    },
    "best_cvm": {
        "ert": [100, 200, 300, 500],
        "window_sizes": ["20", "30", "20 50", "30 60"],
        "min_distance": [20, 30, 40]
    },
    "best_mozilla_rep": {"no_param": [0]},
    "default_bocpd": {"no_param": [0]},
    "default_cpnp": {"no_param": [0]},
    "default_pelt": {"no_param": [0]},
    "default_amoc": {"no_param": [0]},
    "default_segneigh": {"no_param": [0]},
    "default_binseg": {"no_param": [0]},
    "default_rfpop": {"no_param": [0]},
    "default_ecp": {"no_param": [0]},
    "default_kcpa": {"no_param": [0]},
    "default_wbs": {"no_param": [0]},
    "default_prophet": {"no_param": [0]},
    "default_zero": {"no_param": [0]},
    "default_mongodb": {"no_param": [0]},
    "default_adwin": {"no_param": [0]},
    "default_page_hinkley": {"no_param": [0]},
    "default_chisquare": {"no_param": [0]},
    "default_ewma": {"no_param": [0]},
    "default_kswin": {"no_param": [0]},
    "default_cusum": {"no_param": [0]},
    "default_shewhart": {"no_param": [0]},
    "default_odummy": {"no_param": [0]},
    "default_mosum": {"no_param": [0]},
    "default_sprt": {"no_param": [0]},
    "default_cvm": {"no_param": [0]},
    "default_mozilla_rep": {"no_param": [0]}
}

'''
"best_prophet": {"Nmax": ["max", "default"]},
'''

COMMANDS = {
    "best_amoc": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m AMOC",
    "best_binseg": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m BinSeg -Q {Q}",
    "best_cpnp": "Rscript --no-save --slave {execdir}/R/cpdbench_changepointnp.R -i {datadir}/{dataset}.json -p {penalty} -q {quantiles}",
    "best_ecp": "Rscript --no-save --slave {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json -a {algorithm} --siglvl {siglvl} --minsize {minsize} --alpha {alpha}",
    "best_kcpa": "python3.9 {execdir}/python/cpdbench_kcpa.py -i {datadir}/{dataset}.json --maxcp {maxcp} --minsize {minsize} --kernel {kernel}",
    "best_pelt": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m PELT",
    "best_prophet": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_prophet.py -i {datadir}/{dataset}.json -N {Nmax} --WeeklySeasonality True --DailySeasonality False --ChangepointRange {ChangepointRange} --ChangepointPriorScale {ChangepointPriorScale} --IntervalWidth {IntervalWidth} --growth {growth} --cap 100",
    "best_rfpop": "Rscript --no-save --slave {execdir}/R/cpdbench_rfpop.R -i {datadir}/{dataset}.json -l {loss}",
    "best_segneigh": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m SegNeigh -Q {Q}",
    "best_wbs": "Rscript --no-save --slave {execdir}/R/cpdbench_wbs.R -i {datadir}/{dataset}.json -K {Kmax} --penalty {penalty} -g {integrated}",
    "best_bocpd": "Rscript --no-save --slave {execdir}/R/cpdbench_ocp.R -i {datadir}/{dataset}.json -l {intensity} --prior-a {prior_a} --prior-b {prior_b} --prior-k {prior_k}",
    "best_zero": "python3.9 {execdir}/python/cpdbench_zero.py -i {datadir}/{dataset}.json",
    "best_mongodb": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_mongodb.py -i {datadir}/{dataset}.json --pvalue {pvalue} --permutations {permutations}",
    "best_adwin": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_adwin.py -i {datadir}/{dataset}.json --delta {delta}",
    "best_page_hinkley": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_page_hinkley.py -i {datadir}/{dataset}.json --delta {delta} --threshold {threshold} --min_instances {min_instances} --alpha {alpha} --mode {mode}",
    "best_chisquare": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_chisquare.py -i {datadir}/{dataset}.json --window-size {window_size} --num-bins {num_bins} --p-threshold {p_threshold} --min-distance {min_distance}",
    "best_cusum": "python3.9 {execdir}/python/cpdbench_cusum.py -i {datadir}/{dataset}.json --k {k} --h {h} --init-size {init_size} --min-distance {min_distance}",
    "best_ewma":  "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_ewma.py -i {datadir}/{dataset}.json --alpha {alpha} --threshold {threshold} --init-size {init_size} --min-distance {min_distance} ",
    "best_kswin": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_kswin.py -i {datadir}/{dataset}.json --alpha {alpha} --window-size {window_size} --stat-size {stat_size}",
    "best_shewhart": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_shewhart.py -i {datadir}/{dataset}.json --threshold {threshold} --init-size {init_size} --min-distance {min_distance}",
    "best_odummy": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_odummy.py -i {datadir}/{dataset}.json --trigger-method {trigger_method} --t_0 {t_0} --w {w} --init-size {init_size} --min-distance {min_distance} --seed {seed}",
    "best_mosum": "python3.9 {execdir}/python/cpdbench_mosum.py -i {datadir}/{dataset}.json --window-size {window_size} --threshold {threshold} --min-distance {min_distance}",
    "best_sprt": "python3.9 {execdir}/python/cpdbench_sprt.py -i {datadir}/{dataset}.json --mu0 {mu0} --mu1 {mu1} --sigma {sigma} --threshold {threshold} --min-distance {min_distance}",
    "best_cvm": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_cvm.py -i {datadir}/{dataset}.json --ert {ert} --window-sizes {window_sizes} --min-distance {min_distance}",
    "best_mozilla_rep": "python3.9 {execdir}/python/cpdbench_mozilla_rep.py -i {datadir}/{dataset}.json -a /TCPDBench/analysis/annotations/signatures_attributes.json",
    "default_amoc": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m AMOC",
    "default_binseg": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m BinSeg -Q default",
    "default_cpnp": "Rscript --no-save --slave {execdir}/R/cpdbench_changepointnp.R -i {datadir}/{dataset}.json -p MBIC -q 10",
    "default_pelt": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m PELT",
    "default_segneigh": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p BIC -f mean -t Normal -m SegNeigh -Q default",
    "default_wbs": "Rscript --no-save --slave {execdir}/R/cpdbench_wbs.R -i {datadir}/{dataset}.json -K default -p SSIC -g true",
    "default_prophet": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_prophet.py -i {datadir}/{dataset}.json -N default --WeeklySeasonality True --DailySeasonality False --ChangepointRange 0.8 --ChangepointPriorScale 0.05 --IntervalWidth 0.8 --growth linear --cap 1000",
    "default_rfpop": "Rscript --no-save --slave {execdir}/R/cpdbench_rfpop.R -i {datadir}/{dataset}.json -l Outlier",
    "default_ecp": "Rscript {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json --alpha 2.0 --minsize 5 --algorithm e.divisive --siglvl 0.05 --runs 199",
    "default_kcpa": "python3.9 {execdir}/python/cpdbench_kcpa.py -i {datadir}/{dataset}.json --maxcp 2 --minsize 3 --kernel linear",
    "default_bocpd": "Rscript --no-save --slave {execdir}/R/cpdbench_ocp.R -i {datadir}/{dataset}.json -l 100 --prior-a 1.0 --prior-b 1.0 --prior-k 1.0",
    "default_zero": "python3.9 {execdir}/python/cpdbench_zero.py -i {datadir}/{dataset}.json",
    "default_mongodb": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_mongodb.py -i {datadir}/{dataset}.json",
    "default_adwin": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_adwin.py -i {datadir}/{dataset}.json --delta 0.002",
    "default_page_hinkley": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_page_hinkley.py -i {datadir}/{dataset}.json --delta 0.005 --threshold 50.0 --min_instances 30 --alpha 0.9999 --mode both",
    "default_chisquare": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_chisquare.py -i {datadir}/{dataset}.json --window-size 5.0 --num-bins 10 --p-threshold 0.01 --min-distance 30",
    "default_cusum": "python3.9 {execdir}/python/cpdbench_cusum.py -i {datadir}/{dataset}.json --k 1.0 --h 15.0 --init-size 10.0 --min-distance 30",
    "default_ewma":  "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_ewma.py -i {datadir}/{dataset}.json --alpha 0.3 --threshold 3.0 --init-size 10.0 --min-distance 30",
    "default_shewhart": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_shewhart.py -i {datadir}/{dataset}.json --threshold 3.0 --init-size 10.0 --min-distance 30",
    "default_kswin": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_kswin.py -i {datadir}/{dataset}.json --alpha 0.005 --window-size 100 --stat-size 10",
    "default_odummy": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_odummy.py -i {datadir}/{dataset}.json --trigger-method fixed --t_0 300 --w 0 --init-size 10 --min-distance 30 --seed 42",
    "default_mosum": "python3.9 {execdir}/python/cpdbench_mosum.py -i {datadir}/{dataset}.json --window-size 30 --threshold 3.0 --min-distance 30",
    "default_sprt": "python3.9 {execdir}/python/cpdbench_sprt.py -i {datadir}/{dataset}.json --mu0 0.0 --mu1 1.0 --sigma 1.0 --threshold 15.0 --min-distance 30",
    "default_cvm": "source {execdir}/python/venv/bin/activate && python {execdir}/python/cpdbench_cvm.py -i {datadir}/{dataset}.json --ert 200.0 --window-sizes 20 50 --min-distance 30",
    "default_mozilla_rep": "python3.9 {execdir}/python/cpdbench_mozilla_rep.py -i {datadir}/{dataset}.json -a /TCPDBench/analysis/annotations/signatures_attributes.json",
}

METRICS = {}

SCALARS = {"time": {"best": min}}

RESULT_PRECISION = 15

DATA_DESCRIPTION_CSV = None

REFERENCE_METHOD = None

SIGNIFICANCE_LEVEL = 0.05

###############################################################################
#                                PBS Settings                                 #
###############################################################################
PBS_NODES = 1
PBS_WALLTIME = 360  # Walltime in minutes
PBS_CPUTYPE = None
PBS_CORETYPE = None
PBS_PPN = None
PBS_MODULES = ["mpicopy", "python/3.9.6"]
PBS_EXPORTS = ["PATH=$PATH:/home/%s/.local/bin/abed" % REMOTE_USER]
PBS_MPICOPY = ["datasets", "execs", TASK_FILE]
PBS_TIME_REDUCE = 600  # Reduction of runtime in seconds
PBS_LINES_BEFORE = []
PBS_LINES_AFTER = []