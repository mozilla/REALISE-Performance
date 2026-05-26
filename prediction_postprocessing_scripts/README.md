***Folder Overview***

This folder contains scripts used to analyze data and results from `TCPDBench`. Most importantly, this folder contains the scripts used to run **the voting system**.

The code files have definitions that is obtained by running `python <python_file_path> --help`.

- `mozilla_priority_voting.py` file: It simulates the **Mozilla or Ensemble** voting strategy. This script requires the results of the experiments from `TCPDBench`. This voting strategy considers Mozilla's method detections as true alerts regardless of whether other methods agree with it or not. A consensus (specificed though `argparse`).

- `equal_voting.py` file: It simulates the **Ensemble** voting strategy. This script requires the results of the experiments from `TCPDBench`. Unlike the previous voting strategy, all methods have an equal voting weight, including Mozilla's.

- `group_methods_results.py` file: Running experiments on `TCPDBench` could take multiple days for some CPDs with a big hyper parameter search space. That is why experiments of different CPD methods could run separately. Once experiments are concluded, their respective files are extracted from the Docker container on which the experiments ran on. In order to group the experiments' results of all the methods into one coherent experiments folder, we need to run `group_methods_results.py`.

- `handpick_specific_methods.py` and `handpick_specific_signatures.py` files: Upon running multiple CPD methods in one go on `TCPDBench`, the experiments results will be structured as follows:
```
experiments_results/
└── timeseries1/
    ├── best_cpd1/
    ├── best_cpd2/
    ├── default_cpd1/
    └── default_cpd2/
        └── 95af7f836174866e.json
....
```
Where `experiments_results/` represents the experiments results of a specific timeseries, `best_cpd1/` Contains the results of the CPD1 method using all combinations of all hyperparameters, `default_cpd1/` contains the results of the CPD2 method using the default setup of CPD1, and so on and so forth.
 
So in order to separate the experiments results of specific change point detection methods in another folder for whatever reason, `handpick_specific_methods.py` could be used for that purpose.
Otherwise, in order to separate specific timeseries results, `handpick_specific_signatures.py` could be used. 

- `handpick_best_configuration.py` file: Given hyper parameter search space, experiments on a given method will produce various results. This script hanpicks the hyper parameter configuration associated with the best F1 score on average as defined in [this](https://arxiv.org/abs/2003.06222) paper. Apart from the experiments results directory produced by `TCPDBench`, this script also requires the usage of the summary directory produced by `TCPDBench` upon calculating performance metrics.