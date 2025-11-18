# Extending the Benchmark
## Python
When adding a method in Python, you can start with the 
[cpdbench_zero.py](./execs/python/cpdbench_zero.py) file as a template, as 
this contains most of the boilerplate code. A script should take command line 
arguments where ``-i/--input`` marks the path to a dataset file and optionally 
can take further command line arguments for hyperparameter settings. 
Specifying these items from the command line facilitates reproducibility.

## R
Adding a method implemented in R to the benchmark can be done similarly to how 
it is done for Python. Again, the input file path and the hyperparameters are 
specified by command line arguments, which are parsed using 
[argparse](https://cran.r-project.org/web/packages/argparse/index.html). For R 
scripts we use a number of utility functions in the 
[utils.R](./execs/R/utils.R) file. To reliably load this file you can use the 
``load.utils()`` function available in all R scripts.

## Adding the method to the experimental configuration
When you've written the command line script to run your method and verified 
that it works correctly, it's time to add it to the experiment configuration. 
For this, we'll have to edit the [abed_conf.py](./abed_conf.py) file.

1. To add your method, located the ``METHODS`` list in the configuration file 
   and add an entry ``best_<yourmethod>`` and ``default_<yourmethod>``, 
   replacing ``<yourmethod>`` with the name of your method (without spaces or 
   underscores).
2. Next, add the method to the ``PARAMS`` dictionary. This is where you 
   specify all the hyperparameters that your method takes (for the ``best`` 
   experiment). The hyperparameters are specified with a name and a list of 
   values to explore (see the current configuration for examples). For the 
   default experiment, add an entry ``"default_<yourmethod>" : {"no_param": 
   [0]}``. This ensures it will be run without any parameters.
3. Finally, add the command that needs to be executed to run your method to 
   the ``COMMANDS`` dictionary. You'll need an entry for ``best_<yourmethod>`` 
   and for ``default_<yourmethod>``. Please use the existing entries as 
   examples. Methods implemented in R are run with Rscript. The ``{execdir}``, 
   ``{datadir}``, and ``{dataset}`` values will be filled in by abed based on 
   the other settings. Use curly braces to specify hyperparameters, matching 
   the names of the fields in the ``PARAMS`` dictionary.

## Dependencies
If your method needs external R or Python packages to operate, you can add 
them to the respective dependency lists.

* For R, simply add the package name to the [Rpackages.txt](./Rpackages.txt) 
  file. Next, run ``make clean_R_venv`` and ``make R_venv`` to add the package 
  to the R virtual environment. It is recommended to be specific in the 
  version of the package you want to use in the ``Rpackages.txt`` file, for 
  future reference and reproducibility.
* For Python, individual methods use individual virtual environments, as can 
  be seen from the examples. These virtual environments 
  need to be activated in the ``COMMANDS`` section of the ``abed_conf.py`` 
  file. Setting up these environments is done through the Makefile. Simply add 
  a ``requirements.txt`` file in your package similarly to what is done for 
  mongodb, copy and edit the corresponding lines in the Makefile, 
  and run ``make venv_<yourmethod>`` to build the virtual environment.